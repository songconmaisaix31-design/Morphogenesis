"""Fixed-size swarm graph. Scheduling/checkpoints belong to LangGraph."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import time
from typing import Any, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from pydantic import JsonValue

from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope, MsgType
from contracts.protocols import EventStore, Executor, ResultStore, TopologyEngine, Verifier
from contracts.provenance import Acceptance, Provenance
from contracts.resolution import Gene, Metabolism
from contracts.results import TaskResult, Verification
from contracts.runtime import RunConfig


class UnknownExecution(RuntimeError):
    """An existing intent without a trusted checkpoint must not be re-executed."""


class State(TypedDict, total=False):
    task_id: str
    attempt: dict[str, Any]
    genes: list[dict[str, Any]]
    result: dict[str, Any]
    adopted_gene_ids: list[str]
    stop_reason: str


class Runtime:
    """Use inside the lifetime of an official SqliteSaver context manager.

    A run has one task and at most one paid invocation. Explicit new runs require
    caller authorization/budget review; there is no automatic retry or loop.
    Resume never injects new state and never rewinds checkpoints.
    """

    def __init__(self, *, config: RunConfig, saver: SqliteSaver, events: EventStore,
                 results: ResultStore, topology: TopologyEngine, metabolism: Metabolism,
                 executor: Executor, verifier: Verifier, members: list[AgentId],
                 reviewer: AgentId, provenance: Provenance = "live",
                 bind_experience: Callable[[AttemptId, list[str]], None] | None = None,
                 adopted_genes: Callable[[TaskResult], list[str]] | None = None,
                 topology_feedback: Callable[[Envelope, bool], None] | None = None,
                 stop_requested: Callable[[], bool] | None = None,
                 pause_after_execute: bool = False,
                 on_event: Callable[[Envelope], None] | None = None) -> None:
        if reviewer.role != "reviewer" or reviewer in members:
            raise ValueError("independent reviewer must be outside the executor member set")
        if not members or any(member.role != "builder" for member in members):
            raise ValueError("fixed executor pool must contain builders")
        self.config, self.events, self.results = config, events, results
        self.topology, self.metabolism = topology, metabolism
        self.executor, self.verifier = executor, verifier
        self.members, self.reviewer, self.provenance = members, reviewer, provenance
        self.bind_experience, self.adopted_genes = bind_experience, adopted_genes
        self.topology_feedback = topology_feedback
        self.stop_requested = stop_requested or (lambda: False)
        self.on_event = on_event
        self.graph_config: RunnableConfig = {"configurable": {"thread_id": config.run_id}}
        builder = StateGraph(State)
        builder.add_node("select", self._select)
        builder.add_node("execute", self._execute)
        builder.add_node("review", self._review)
        builder.add_node("feedback", self._feedback)
        builder.add_edge(START, "select")
        builder.add_edge("select", "execute")
        builder.add_edge("execute", "review")
        builder.add_edge("review", "feedback")
        builder.add_edge("feedback", END)
        self.graph = builder.compile(checkpointer=saver,
                                     interrupt_after=["execute"] if pause_after_execute else None)

    def start(self, task_id: str) -> State:
        if self.graph.get_state(self.graph_config).values or self.events.events(self.config.run_id):
            raise ValueError("run already exists; resume it, do not start again")
        return cast(State, self.graph.invoke({"task_id": task_id}, self.graph_config, durability="sync"))

    def resume(self) -> State:
        if not self.graph.get_state(self.graph_config).values:
            raise ValueError("no durable checkpoint for this run")
        # Topology is per-run/in-memory. Rehydrate using the existing durable
        # independent verdicts; its attempt/message dedup makes this safe for
        # both a new engine and an already-live engine.
        for event in self.events.events(self.config.run_id):
            if event.msg_id != f"{self.config.run_id}:reviewed":
                continue
            result = TaskResult.model_validate(event.payload["result"])
            if result.status in {"succeeded", "failed"}:
                if self.topology_feedback:
                    self.topology_feedback(event, result.status == "succeeded")
                else:
                    self.topology.record(result.attempt, result.status == "succeeded")
        return cast(State, self.graph.invoke(None, self.graph_config, durability="sync"))

    def _event(self, attempt: AttemptId, stage: str, seq: int, kind: MsgType,
               payload: dict[str, JsonValue], *, artifact: str | None = None,
               sender: AgentId | None = None) -> Envelope:
        key = f"{self.config.run_id}:{stage}"
        for previous in self.events.events(self.config.run_id):
            if previous.msg_id == key:
                if previous.attempt != attempt or previous.payload != payload:
                    raise ValueError("conflicting replay of runtime event")
                return previous
        event = Envelope(run_id=self.config.run_id, msg_id=key, msg_type=kind,
                         sender=sender or attempt.agent, receiver="broadcast",
                         task_id=attempt.task_id, attempt=attempt, seq=seq, ts=time.time(),
                         provenance=self.provenance, payload=payload, artifact_uri=artifact)
        self.events.append_event(event)
        if self.on_event:
            self.on_event(event)
        return event

    def _select(self, state: State) -> State:
        selected = self.topology.select(self.members)
        if selected is None or selected not in self.members:
            raise ValueError("topology did not select an eligible builder")
        attempt = AttemptId(task_id=state["task_id"], agent=selected, attempt=0)
        if self.bind_experience:
            self.bind_experience(attempt, ["python", "repair", "boundary"])
        genes = [self.metabolism.resolve(gene.ref)
                 for gene in self.metabolism.inject(selected, self.config.gene_budget)]
        if self.provenance == "live" and any(gene.provenance != "live" for gene in genes):
            raise ValueError("mock/replay genes cannot enter a live run")
        self._event(attempt, "selected", 0, MsgType.INTENT,
                    {"stage": "selected", "selected": selected.model_dump(mode="json"),
                     "topology": [pipe.model_dump(mode="json") for pipe in self.topology.snapshot()],
                     "injected_genes": [gene.model_dump(mode="json") for gene in genes]})
        return {"attempt": attempt.model_dump(mode="json"),
                "genes": [gene.model_dump(mode="json") for gene in genes]}

    def _execute(self, state: State) -> State:
        attempt = AttemptId.model_validate(state["attempt"])
        if self.stop_requested():
            result = TaskResult(run_id=self.config.run_id, task_id=attempt.task_id,
                                attempt=attempt, status="interrupted", provenance=self.provenance,
                                acceptance=Acceptance(provenance=self.provenance),
                                verdict=Verification(summary="manual stop before execution"))
            return {"result": result.model_dump(mode="json"), "stop_reason": "manual"}
        key = f"{self.config.run_id}:execute_intent"
        if any(event.msg_id == key for event in self.events.events(self.config.run_id)):
            raise UnknownExecution("execution intent exists; external effect/checkpoint uncertain; no retry")
        # A durable EventStore uniqueness constraint arbitrates concurrent starts.
        intent = Envelope(run_id=self.config.run_id, msg_id=key, msg_type=MsgType.INTENT,
                          sender=attempt.agent, receiver=self.reviewer, task_id=attempt.task_id,
                          attempt=attempt, seq=1, ts=time.time(), provenance=self.provenance,
                          payload={"stage": "execute_intent", "max_invocations": 1,
                                   "max_tokens": self.config.max_tokens,
                                   "max_cost_usd": self.config.max_cost_usd})
        if not self.events.append_event(intent):
            raise UnknownExecution("execution intent already exists; no retry")
        if self.on_event:
            self.on_event(intent)
        result = self.executor.execute(attempt, self.config,
                                       [Gene.model_validate(value) for value in state["genes"]])
        if (result.attempt != attempt or result.run_id != self.config.run_id
                or result.provenance != self.provenance):
            raise ValueError("executor returned mismatched identity/provenance")
        adopted = self.adopted_genes(result) if self.adopted_genes and result.status == "pending_review" else []
        supplied = {Gene.model_validate(value).ref.gene_id for value in state["genes"]}
        if not set(adopted).issubset(supplied):
            raise ValueError("executor adopted a gene which was not injected")
        self.results.save_result(result)
        self._event(attempt, "executed", 2, MsgType.RESULT,
                    {"stage": "executed", "result": result.model_dump(mode="json"),
                     "adopted_gene_ids": list(adopted)}, artifact=result.artifact_uri)
        stop = "unknown_usage" if result.usage.tokens is None or result.usage.cost_usd is None else ""
        return {"result": result.model_dump(mode="json"), "adopted_gene_ids": adopted, "stop_reason": stop}

    def _review(self, state: State) -> State:
        result = TaskResult.model_validate(state["result"])
        if result.status != "pending_review":
            return {}
        from orchestration.codex import task_workspace
        from orchestration.sample_policy import validate_sample

        root = task_workspace(self.config)
        validate_sample((root / "sample.py").read_text(encoding="utf-8"))
        verdict = self.verifier.verify(self.config.workspace, self.reviewer)
        if verdict.reviewer != self.reviewer:
            raise ValueError("verifier returned another reviewer identity")
        status = "succeeded" if verdict.passed is True else "failed" if verdict.passed is False else "insufficient_evidence"
        payload = result.model_dump(mode="json")
        payload.update(status=status, verdict=verdict.model_dump(mode="json"),
                       acceptance=Acceptance(
                           provenance=self.provenance,
                           interface_live=result.acceptance.interface_live,
                           task_live=("passed" if status == "succeeded" else "failed")
                           if self.provenance == "live" else "not_run").model_dump(mode="json"))
        reviewed = TaskResult.model_validate(payload)
        self.results.save_result(reviewed)
        self._event(result.attempt, "reviewed", 3, MsgType.RESULT,
                    {"stage": "reviewed", "result": reviewed.model_dump(mode="json")},
                    artifact=reviewed.artifact_uri, sender=self.reviewer)
        return {"result": reviewed.model_dump(mode="json")}

    def _feedback(self, state: State) -> State:
        result = TaskResult.model_validate(state["result"])
        # Unknown execution or incomplete evidence is not a failed repair.
        if result.status in {"succeeded", "failed"}:
            if self.topology_feedback:
                reviewed = next(event for event in self.events.events(self.config.run_id)
                                if event.msg_id == f"{self.config.run_id}:reviewed")
                self.topology_feedback(reviewed, result.status == "succeeded")
            else:
                self.topology.record(result.attempt, result.status == "succeeded")
        adopted = state.get("adopted_gene_ids", []) if result.status == "succeeded" else []
        for gene_id in adopted:
            self.metabolism.mark_used(gene_id, result.attempt)
        self._event(result.attempt, "feedback", 4, MsgType.SIGNAL,
                    {"stage": "feedback", "status": result.status,
                     "adopted_gene_ids": list(adopted),
                     "stop_reason": state.get("stop_reason", ""),
                     "topology": [pipe.model_dump(mode="json") for pipe in self.topology.snapshot()]},
                    sender=self.reviewer)
        return {}


def adoption_reader(evidence_dir: str | Path) -> Callable[[TaskResult], list[str]]:
    """Local bridge for executor proposal metadata without changing T0 contracts."""
    from orchestration.codex import Proposal

    def read(result: TaskResult) -> list[str]:
        if result.status != "pending_review":
            return []
        return Proposal.model_validate_json(
            (Path(evidence_dir) / "proposal.json").read_text(encoding="utf-8")).adopted_gene_ids

    return read
