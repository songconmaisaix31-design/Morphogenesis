"""Explicit one-call live exercise entry point; never runs a campaign or retries.

Each initial invocation requires an operator-approved budget. A continuation
reopens the SQLite checkpoint and performs only the remaining graph nodes.
Local raw CLI/verification evidence is kept under --root, outside Git.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts.messages import Envelope
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult
from contracts.runtime import RunConfig
from metabolism import LocalMetabolism
from orchestration.codex import CodexExecutor, Proposal
from orchestration.events import export_events
from orchestration.runtime import Runtime, adoption_reader
from orca_provision import FixedProvisioner
from persistence import SQLiteStore
from topology import Connection, TopologyEngine


def prior_experience(root: Path) -> Gene:
    result = TaskResult.model_validate_json((root / "result.json").read_text(encoding="utf-8"))
    if result.provenance != "live" or result.status != "succeeded" or result.acceptance.task_live != "passed":
        raise ValueError("experience requires a previously verified live task")
    proposal = Proposal.model_validate_json((root / "cli/proposal.json").read_text(encoding="utf-8"))
    return Gene(ref=GeneRef(gene_id=f"verified-repair-{result.run_id}"),
                signals_match=["python", "repair", "boundary"], strategy=[proposal.summary],
                verification=[result.verdict.summary], source_attempt=result.attempt, provenance="live")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--model", default="gpt-5.6-luna")
    parser.add_argument("--pause-after-execute", action="store_true")
    parser.add_argument("--continue", dest="continuation", action="store_true")
    parser.add_argument("--experience", type=Path)
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--max-cost-usd", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    root = (args.root or Path(tempfile.mkdtemp(prefix="morph-t2-live-"))).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.continuation:
        config = RunConfig.model_validate_json((root / "config.json").read_text(encoding="utf-8"))
    else:
        if any(root.iterdir()):
            raise ValueError("new live run requires an empty evidence root")
        workspace = prepare_workspace(root / "task")
        config = RunConfig(run_id=f"t2-{uuid4().hex}", workspace=str(workspace), writable_paths=["sample.py"],
                           max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd,
                           max_retries=0, no_progress_limit=1, timeout_seconds=args.timeout)
        (root / "config.json").write_text(config.model_dump_json(indent=2), encoding="utf-8")
    store = SQLiteStore(root / "metadata.db")
    metabolism = LocalMetabolism(store, config.run_id)
    if args.experience and not args.continuation:
        metabolism.ingest(prior_experience(args.experience.resolve()))
    provision = FixedProvisioner(5, roles=("planner", "builder", "builder", "reviewer", "aggregator")).provision(config.run_id, 5)
    store.save_provision(provision)
    planner = next(member for member in provision.members if member.role == "planner")
    reviewer = next(member for member in provision.members if member.role == "reviewer")
    members = [member for member in provision.members if member.role == "builder"]
    routing_path = root / "routing.json"
    if args.continuation and routing_path.exists():
        routing = json.loads(routing_path.read_text(encoding="utf-8"))
        connections = [Connection.model_validate(value) for value in routing["connections"]]
        prior_feedback = [Envelope.model_validate(value) for value in routing["prior_feedback"]]
    else:
        # Reuse experiment: previous live success must change the next real
        # selection, from builder 1 to builder 0, under this declared policy.
        connections = [Connection(src=planner, dst=members[0], weight=1),
                       Connection(src=planner, dst=members[1], weight=1.5 if args.experience else 0.9)]
        prior_feedback = []
        if args.experience:
            for line in (args.experience / "events.jsonl").read_text(encoding="utf-8").splitlines():
                event = Envelope.model_validate_json(line)
                if event.payload.get("stage") == "reviewed":
                    previous = TaskResult.model_validate(event.payload["result"])
                    if previous.provenance == "live" and previous.status == "succeeded":
                        prior_feedback.append(event)
    topology = TopologyEngine(planner, connections)
    before_feedback = topology.select(members)
    for event in prior_feedback:
        topology.record_feedback(event, True, route_source=planner, route_target=event.attempt.agent)
    after_feedback = topology.select(members)
    routing = {"connections": [connection.model_dump(mode="json") for connection in connections],
               "prior_feedback": [event.model_dump(mode="json") for event in prior_feedback],
               "before_feedback": before_feedback.model_dump(mode="json") if before_feedback else None,
               "after_feedback": after_feedback.model_dump(mode="json") if after_feedback else None}
    routing_path.write_text(json.dumps(routing, indent=2), encoding="utf-8")
    executor = CodexExecutor(root / "cli", model=args.model,
                             stop_requested=lambda: (root / "STOP").exists())

    def record(feedback: Envelope, success: bool) -> None:
        topology.record_feedback(feedback, success, route_source=planner, route_target=feedback.attempt.agent)

    try:
        with SqliteSaver.from_conn_string(str(root / "checkpoints.db")) as saver:
            app = Runtime(config=config, saver=saver, events=store, results=store,
                          topology=topology, metabolism=metabolism, executor=executor,
                          verifier=SampleVerifier(root / "review"), members=members, reviewer=reviewer,
                          bind_experience=metabolism.bind_attempt, adopted_genes=adoption_reader(root / "cli"),
                          topology_feedback=record, stop_requested=lambda: (root / "STOP").exists(),
                          pause_after_execute=args.pause_after_execute and not args.continuation)
            state = app.resume() if args.continuation else app.start(f"repair-{config.run_id}")
            result = TaskResult.model_validate(state["result"])
            (root / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
            summary = {"root": str(root), "result": result.model_dump(mode="json"),
                       "next": list(app.graph.get_state(app.graph_config).next),
                       "adopted_gene_ids": state.get("adopted_gene_ids", []),
                       "stop_reason": state.get("stop_reason"),
                       "routing": routing,
                       "execution_intents": sum(event.payload.get("stage") == "execute_intent"
                                                for event in store.events(config.run_id)),
                       "note": "CLI token/dollar ceilings cannot be enforced mid-call; cost remains unknown; no automatic next call"}
            (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(json.dumps(summary))
            return 0 if result.status in {"succeeded", "pending_review"} else 2
    finally:
        export_events(store, config.run_id, root / "events.jsonl")
        (root / "genes.json").write_text(json.dumps(
            [gene.model_dump(mode="json") for gene in metabolism.snapshot()], indent=2), encoding="utf-8")
        (root / "adoption.json").write_text(json.dumps(
            [record.model_dump(mode="json") for record in metabolism.usage_records()], indent=2), encoding="utf-8")
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
