"""Two explicitly authorized NEW repairs through the existing LangGraph Runtime.

This presentation adapter never resumes/retries paid execution. Reopening saved
snapshots is read-only replay. The existing one-task acceptance CLI is unchanged.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import tempfile
import time
from typing import Literal
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import Field, model_validator

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts.base import Contract
from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope
from contracts.protocols import Executor, PipeState
from contracts.provenance import Acceptance, CheckState, Provenance
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult, Verification
from contracts.runtime import RunConfig
from metabolism import LocalMetabolism
from metabolism.models import UseRecord
from orchestration.codex import CodexExecutor, Proposal
from orchestration.events import export_events
from orchestration.gateway import EVOMAP_MODEL, GatewayExecutor
from orchestration.rehearsal_models import (
    Checkpoint, Checkpoints, ExecutorKind, MemberAvailability, RehearsalDocument,
    RehearsalSnapshot, RoutingFact, Stage,
)
from orchestration.runtime import Runtime, adoption_reader
from orca_provision import FixedProvisioner
from persistence import SQLiteStore
from topology import Connection, TopologyEngine

TaskName = Literal["repair", "recovery"]


class RehearsalOptions(Contract):
    root: Path
    executor: ExecutorKind = "codex"
    model: str = "gpt-5.6-luna"
    mode: Literal["auto", "manual"] = "auto"
    tau_seconds: float = Field(default=10, gt=0)
    archive_threshold: float = Field(default=0.2, gt=0, lt=1)
    stage_delay: float = Field(default=2, ge=0, le=60)
    tick_seconds: float = Field(default=1, gt=0, le=60)
    timeout_seconds: float = Field(default=120, gt=0)
    max_tokens: int = Field(default=20000, gt=0)
    max_cost_usd: float = Field(default=1, gt=0)
    authorized_tasks: list[TaskName] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def executor_model_default(cls, value: object) -> object:
        if isinstance(value, dict) and value.get("executor") == "evomap" and "model" not in value:
            return {**value, "model": EVOMAP_MODEL}
        return value


ExecutorFactory = Callable[[Path, RehearsalOptions], Executor]


def _checkpoint_view(verifier: SampleVerifier, verdict: Verification,
                     provenance: Provenance) -> Checkpoints:
    names: tuple[Literal["clamp", "mean", "unique"], ...] = ("clamp", "mean", "unique")
    checks = [Checkpoint(name=name, passed=verifier.last_checks.get(name)) for name in names]
    passed = sum(check.passed is True for check in checks)
    return Checkpoints(checks=checks, passed_count=passed, ratio=passed / 3,
                       verification=verdict, provenance=provenance)


def read_rehearsal(path: str | Path, *, replay: bool = False) -> RehearsalDocument:
    """Validate the shared contract, optionally downgrade all sources to replay.

    No SQLite, executor, input, sleeps, or writes are involved. Historical times,
    verdicts, and unknown costs remain unchanged; replay is never live acceptance.
    """
    source = Path(path).resolve()
    document = RehearsalDocument.model_validate_json(source.read_text(encoding="utf-8"))
    if not replay:
        return document
    origin = document.original_run_uri or source.as_uri()
    history: list[RehearsalSnapshot] = []
    for snapshot in document.history:
        data = snapshot.model_dump(mode="json")
        data["provenance"] = "replay"
        data["message"] = f"Replay of {document.mode} source. {snapshot.message}"
        data["acceptance"] = Acceptance(provenance="replay", original_run_uri=origin,
                                        contract_local="passed").model_dump(mode="json")
        if snapshot.checkpoints:
            data["checkpoints"] = {**snapshot.checkpoints.model_dump(mode="json"), "provenance": "replay"}
        data["genes"] = [{**gene.model_dump(mode="json"), "provenance": "replay",
                          "original_run_uri": origin} for gene in snapshot.genes]
        data["adoptions"] = [{**record.model_dump(mode="json"), "provenance": "replay"}
                             for record in snapshot.adoptions]
        data["results"] = [{**result.model_dump(mode="json"), "provenance": "replay",
                            "original_run_uri": origin,
                            "acceptance": data["acceptance"]} for result in snapshot.results]
        history.append(RehearsalSnapshot.model_validate(data))
    return RehearsalDocument(rehearsal_id=document.rehearsal_id, mode="replay",
                             original_run_uri=origin, current=history[-1], history=history)


class Rehearsal:
    """A fixed, linear demonstration script; LangGraph still owns task execution."""

    def __init__(self, options: RehearsalOptions, *, provenance: Provenance = "live",
                 executor_factory: ExecutorFactory | None = None,
                 wait_for_offline: Callable[[str], str] = input,
                 on_snapshot: Callable[[RehearsalDocument], None] | None = None) -> None:
        if provenance == "replay":
            raise ValueError("use read_rehearsal(replay=True), not an executor, for replay")
        if provenance == "live" and sorted(options.authorized_tasks) != ["recovery", "repair"]:
            raise ValueError("explicit authorization required for both NEW tasks: repair and recovery")
        if provenance == "mock" and executor_factory is None:
            raise ValueError("mock rehearsal requires an explicit fixture executor")
        root = options.root.resolve()
        temporary = Path(tempfile.gettempdir()).resolve()
        if root == temporary or not root.is_relative_to(temporary) or options.root.is_symlink():
            raise ValueError("rehearsal requires a new private root under OS TEMP")
        root.mkdir(parents=True, exist_ok=True)
        if any(root.iterdir()):
            raise ValueError("new rehearsal requires an empty root; use --replay to read existing evidence")
        self.options, self.root, self.provenance = options, root, provenance
        self.wait_for_offline, self.on_snapshot = wait_for_offline, on_snapshot
        self.executor_factory = executor_factory or (self._gateway if options.executor == "evomap" else self._codex)
        self.rehearsal_id = f"rehearsal-{uuid4().hex}"
        self.store = SQLiteStore(root / "metadata.db")
        provision = FixedProvisioner(5, roles=("planner", "builder", "builder", "reviewer", "aggregator")).provision(
            self.rehearsal_id, 5)
        # FixedProvisioner describes local capacity; fixtures retain mock provenance.
        provision = provision.model_copy(update={"provenance": provenance})
        self.store.save_provision(provision)
        self.planner = next(member for member in provision.members if member.role == "planner")
        self.reviewer = next(member for member in provision.members if member.role == "reviewer")
        builders = [member for member in provision.members if member.role == "builder"]
        self.members = [MemberAvailability(agent=member, changed_at=time.time()) for member in provision.members]
        self.topology = TopologyEngine(self.planner, [
            Connection(src=self.planner, dst=builders[0], weight=1),
            Connection(src=self.planner, dst=builders[1], weight=0.9),
        ])
        self.metabolism = LocalMetabolism(self.store, self.rehearsal_id, provenance=provenance,
                                          tau_seconds=options.tau_seconds,
                                          archive_threshold=options.archive_threshold)
        self.histories: list[RehearsalSnapshot] = []
        self.results: list[TaskResult] = []
        self.run_ids: list[str] = []
        self.adoptions: list[UseRecord] = []
        self.checkpoints: Checkpoints | None = None
        self.routing = RoutingFact(task_id=f"repair-{self.rehearsal_id}", eligible_members=builders)
        self.task_description = "修复 sample.py 的 clamp、mean、unique 三个已知 bug（任务一）"
        self.verifier = SampleVerifier(root / "initial-review")

    def _codex(self, evidence: Path, options: RehearsalOptions) -> Executor:
        return CodexExecutor(evidence, model=options.model, stop_requested=self._stopped)

    def _gateway(self, evidence: Path, options: RehearsalOptions) -> Executor:
        return GatewayExecutor(evidence, model=options.model, stop_requested=self._stopped)

    def _stopped(self) -> bool:
        return (self.root / "STOP").exists()

    def _eligible(self) -> list[AgentId]:
        return [member.agent for member in self.members if member.available and member.agent.role == "builder"]

    def _wait(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self._stopped():
                raise InterruptedError("operator STOP; no additional calls")
            time.sleep(min(0.1, max(0, deadline - time.monotonic())))

    def _emit(self, stage: Stage, message: str = "", failure: str | None = None) -> RehearsalDocument:
        now = time.time()
        self.metabolism.decay_weights(now)
        genes = self.metabolism.snapshot()
        retrievable: list[str] = []
        for gene in genes:
            try:
                self.metabolism.resolve(gene.ref)
                retrievable.append(gene.ref.gene_id)
            except KeyError:
                if gene.archived_at is None:
                    raise
        available = {member.agent for member in self.members if member.available}
        # Presentation-only availability overlay; policy edges retain their weights/state.
        pipes = [PipeState.model_validate({**pipe.model_dump(),
                                           "active": pipe.active and pipe.dst in available})
                 for pipe in self.topology.snapshot()]
        costs = [result.usage.cost_usd for result in self.results]
        cost = sum(value for value in costs if value is not None) if costs and all(
            value is not None for value in costs) else None
        interface: CheckState = "not_run"
        task: CheckState = "not_run"
        if self.provenance == "live":
            interfaces = [result.acceptance.interface_live for result in self.results]
            interface = ("blocked" if "blocked" in interfaces else "failed" if "failed" in interfaces
                         else "passed" if interfaces and all(value == "passed" for value in interfaces)
                         else "not_run")
            task = ("passed" if stage == "completed" else "failed"
                    if any(result.status == "failed" for result in self.results) else "blocked"
                    if stage == "failed" else "not_run")
        snapshot = RehearsalSnapshot(
            executor=self.options.executor, model=self.options.model,
            sequence=len(self.histories), stage=stage, at=now, task_id=self.routing.task_id,
            task_description=self.task_description, provenance=self.provenance,
            acceptance=Acceptance(provenance=self.provenance, contract_local="passed",
                                  interface_live=interface, task_live=task),
            checkpoints=self.checkpoints, members=list(self.members), pipes=pipes, routing=self.routing,
            genes=genes, adoptions=list(self.adoptions), results=list(self.results),
            retrievable_gene_ids=retrievable, tau_seconds=self.options.tau_seconds,
            archive_threshold=self.options.archive_threshold,
            model_calls_started=sum(event.payload.get("stage") == "execute_intent"
                                    for run_id in self.run_ids for event in self.store.events(run_id)),
            cost_usd=cost, message=message, failure=failure,
        )
        self.histories.append(snapshot)
        document = RehearsalDocument(rehearsal_id=self.rehearsal_id, mode=self.provenance,
                                     current=snapshot, history=list(self.histories))
        pending = self.root / "rehearsal.next.json"
        pending.write_text(document.model_dump_json(indent=2), encoding="utf-8")
        pending.replace(self.root / "rehearsal.json")
        if self.on_snapshot:
            self.on_snapshot(document)
        if failure is None and stage != "completed":
            self._wait(self.options.stage_delay)
        return document

    def _observe(self, event: Envelope) -> None:
        phase = event.payload.get("stage")
        recovery = len(self.run_ids) == 2
        if phase == "selected":
            self.routing = self.routing.model_copy(update={"selected_attempt": event.attempt})
        if phase == "execute_intent":
            self._emit("recovery_selected" if recovery else "repair_selected",
                       f"LangGraph 已按有效成员列表选中实例；本任务只有一次 {self.options.executor} 调用")
        elif phase == "reviewed":
            result = TaskResult.model_validate(event.payload["result"])
            self.results.append(result)
            self.checkpoints = _checkpoint_view(self.verifier, result.verdict, self.provenance)
            self._emit("recovery_reviewed" if recovery else "repair_reviewed", "外部固定 unittest 已完成独立复核")
        elif phase == "feedback" and any(result.attempt == event.attempt for result in self.results):
            self.adoptions.extend(record for record in self.metabolism.usage_records() if record not in self.adoptions)
            self._emit("gene_adopted" if recovery and self.adoptions else (
                "recovery_reviewed" if recovery else "repair_reviewed"),
                "独立结果已反馈至拓扑；只有明确采用的已注入 Gene 才刷新权重")

    def _task(self, name: TaskName, workspace: Path) -> TaskResult:
        if self._stopped():
            raise InterruptedError("operator STOP before new task")
        task_root = workspace.parent
        evidence = task_root / ("gateway" if self.options.executor == "evomap" else "cli")
        run_id = f"{self.rehearsal_id}-{name}"
        self.run_ids.append(run_id)
        config = RunConfig(run_id=run_id, workspace=str(workspace), writable_paths=["sample.py"],
                           max_tokens=self.options.max_tokens, max_cost_usd=self.options.max_cost_usd,
                           max_retries=0, no_progress_limit=1, timeout_seconds=self.options.timeout_seconds)
        (task_root / "config.json").write_text(config.model_dump_json(indent=2), encoding="utf-8")
        self.metabolism = LocalMetabolism(self.store, run_id, provenance=self.provenance,
                                          tau_seconds=self.options.tau_seconds,
                                          archive_threshold=self.options.archive_threshold)
        self.verifier = SampleVerifier(task_root / "review")

        def feedback(event: Envelope, success: bool) -> None:
            self.topology.record_feedback(event, success, route_source=self.planner, route_target=event.attempt.agent)

        try:
            with SqliteSaver.from_conn_string(str(self.root / "checkpoints.db")) as saver:
                app = Runtime(config=config, saver=saver, events=self.store, results=self.store,
                              topology=self.topology, metabolism=self.metabolism,
                              executor=self.executor_factory(evidence, self.options),
                              verifier=self.verifier, members=self._eligible(), reviewer=self.reviewer,
                              provenance=self.provenance, bind_experience=self.metabolism.bind_attempt,
                              adopted_genes=adoption_reader(evidence), topology_feedback=feedback,
                              stop_requested=self._stopped, on_event=self._observe)
                state = app.start(self.routing.task_id)
            result = TaskResult.model_validate(state["result"])
            if result not in self.results:
                self.results.append(result)
            (task_root / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
            if result.status != "succeeded":
                raise RuntimeError(f"{name}: {result.status}; {result.verdict.summary}; no retry")
            proposal = Proposal.model_validate_json((evidence / "proposal.json").read_text(encoding="utf-8"))
            gene = Gene(ref=GeneRef(gene_id=f"verified-{run_id}"), provenance=self.provenance,
                        signals_match=["python", "repair", "boundary"],
                        strategy=[proposal.summary, "Independently verified sample repair:\n" + proposal.content],
                        verification=[result.verdict.summary], source_attempt=result.attempt)
            self.metabolism.ingest(gene)
            (task_root / "gene.json").write_text(gene.model_dump_json(indent=2), encoding="utf-8")
            self._emit("gene_generated", "本任务成功 proposal 与 source_attempt 已生成本地 Gene，待发布")
            if result.usage.tokens is None:
                raise RuntimeError(f"{name}: token usage unknown; no additional calls")
            # Cost remains unknown. Task two is a separately authorized NEW task;
            # it is never a continuation or retry of this task's execution.
            return result
        finally:
            export_events(self.store, run_id, task_root / "events.jsonl")

    def run(self) -> RehearsalDocument:
        try:
            first_workspace = prepare_workspace(self.root / "repair/task")
            initial = self.verifier.verify(str(first_workspace), self.reviewer)
            self.checkpoints = _checkpoint_view(self.verifier, initial, self.provenance)
            self._emit("task_ready", "初始 checkpoint 来自外部固定 unittest，未调用模型")
            if any(check.passed is not False for check in self.checkpoints.checks):
                raise RuntimeError("known broken fixture must independently fail all three checkpoints")
            first = self._task("repair", first_workspace)
            self._emit("awaiting_offline", "两任务之间下线获胜 builder；不杀进程，不声称在途恢复")
            if self.options.mode == "manual":
                self.wait_for_offline("Press Enter to remove the winning logical builder before the NEW recovery task: ")
            if self._stopped():
                raise InterruptedError("operator STOP before member removal")
            removed_at = time.time()
            self.members = [member.model_copy(update={"available": False, "changed_at": removed_at,
                                                      "reason": "operator removed between tasks"})
                            if member.agent == first.attempt.agent else member for member in self.members]
            self.routing = RoutingFact(task_id=f"recovery-{self.rehearsal_id}", eligible_members=self._eligible(),
                                       removed_member=first.attempt.agent, removed_at=removed_at)
            self._emit("member_offline", "获胜 builder 已从新任务有效成员列表移除，原管道展示 inactive")
            self.task_description = "在全新样例副本修复相同三个 bug（新任务二）；只剩一名 builder，独立 reviewer 复核"
            workspace = prepare_workspace(self.root / "recovery/task")
            task = workspace / "TASK.md"
            task.write_text(task.read_text(encoding="utf-8") + "\nThis is a NEW repair in a fresh workspace. "
                            "Use the supplied verified experience when applicable; report its gene ID only "
                            "if you actually apply its strategy.\n", encoding="utf-8")
            self.verifier = SampleVerifier(self.root / "recovery/initial-review")
            self.checkpoints = _checkpoint_view(self.verifier, self.verifier.verify(str(workspace), self.reviewer),
                                                self.provenance)
            self._emit("recovery_ready", "新任务重新从真实坏样例开始；不是重试第一次调用")
            second = self._task("recovery", workspace)
            if second.attempt.agent == first.attempt.agent or second.attempt.agent not in self._eligible():
                raise RuntimeError("recovery did not execute on the remaining eligible builder")
            if not any(record.attempt == second.attempt and record.ref.gene_id == f"verified-{first.run_id}"
                       for record in self.adoptions):
                raise RuntimeError("recovery succeeded but no actual adoption of the first Gene was reported")
            while True:
                document = self._emit("decaying", "真实墙钟衰减；tau 显示在页面，不快进时钟")
                if all(gene.weight < self.options.archive_threshold for gene in document.current.genes):
                    break
                self._wait(self.options.tick_seconds)
            archived = self.metabolism.archive()
            document = self._emit("archived", "已按阈值本地归档，逐一 resolve 验证不可检索；未同步远端")
            if not archived or document.current.retrievable_gene_ids:
                raise RuntimeError("local archival did not remove every generated Gene from retrieval")
            return self._emit("completed", "两次新任务完成；费用未知仍为 null，Hub 待发布，固定成员可用性恢复")
        except (Exception, KeyboardInterrupt) as exc:
            return self._emit("failed", "彩排停止；保留证据，不自动重试或调用下一任务", f"{type(exc).__name__}: {exc}")
        finally:
            self.store.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--mode", choices=["auto", "manual"], default="auto")
    parser.add_argument("--executor", choices=["codex", "evomap"], default="codex")
    parser.add_argument("--model", help="defaults to gpt-5.6-luna or evomap-gpt-5.6-luna for the selected executor")
    parser.add_argument("--authorize-task", action="append", choices=["repair", "recovery"], default=[])
    parser.add_argument("--tau-seconds", type=float, default=10)
    parser.add_argument("--archive-threshold", type=float, default=0.2)
    parser.add_argument("--stage-delay", type=float, default=2)
    parser.add_argument("--tick-seconds", type=float, default=1)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--max-cost-usd", type=float, default=1)
    args = parser.parse_args()
    if args.replay:
        print(read_rehearsal(args.replay, replay=True).model_dump_json(indent=2))
        return 0
    if sorted(args.authorize_task) != ["recovery", "repair"]:
        parser.error("live rehearsal requires --authorize-task repair --authorize-task recovery (two NEW calls)")
    options = RehearsalOptions(
        root=args.root or Path(tempfile.mkdtemp(prefix="morph-rehearsal-")), executor=args.executor,
        model=args.model or (EVOMAP_MODEL if args.executor == "evomap" else "gpt-5.6-luna"),
        mode=args.mode, tau_seconds=args.tau_seconds, archive_threshold=args.archive_threshold,
        stage_delay=args.stage_delay, tick_seconds=args.tick_seconds, timeout_seconds=args.timeout,
        max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd, authorized_tasks=args.authorize_task,
    )
    print(json.dumps({"root": str(options.root.resolve()), "executor": options.executor,
                      "model": options.model, "max_new_calls": 2,
                      "cost_note": "No hard in-flight dollar cap; unknown costs remain null"}), flush=True)
    document = Rehearsal(options).run()
    print(json.dumps({"root": str(options.root.resolve()), "stage": document.current.stage,
                      "failure": document.current.failure, "cost_usd": document.current.cost_usd}))
    return 0 if document.current.stage == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
