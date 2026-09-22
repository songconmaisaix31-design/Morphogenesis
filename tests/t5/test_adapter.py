import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope, MsgType
from contracts.protocols import EventStore
from contracts.provenance import Acceptance
from contracts.resolution import GeneRef
from contracts.protocols import PipeState
from contracts.results import TaskResult, Verification
from metabolism import GeneView, UseRecord
from orchestration.events import export_events
from orchestration.rehearsal_models import MemberAvailability, RehearsalDocument, RehearsalSnapshot, RoutingFact
from viz.adapter import DashboardInputError, empty_dashboard, load_dashboard, load_rehearsal, load_runtime_export


class DashboardAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "demo" / "data").mkdir(parents=True)
        (self.root / "runtime_exports").mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_mock_document_is_labelled_and_cannot_upgrade_live_acceptance(self) -> None:
        path = self.root / "demo" / "data" / "fixture.json"
        path.write_text(json.dumps({"provenance": "mock", "acceptance": {"task_live": "passed"}}), encoding="utf-8")
        with self.assertRaisesRegex(DashboardInputError, "mock/replay"):
            load_dashboard(path, self.root)

    def test_document_input_cannot_claim_to_be_a_live_runtime(self) -> None:
        path = self.root / "demo" / "data" / "claimed-live.json"
        path.write_text(json.dumps({"provenance": "live", "acceptance": {"task_live": "passed"}}), encoding="utf-8")
        with self.assertRaisesRegex(DashboardInputError, "仅用于显式 mock"):
            load_dashboard(path, self.root)

    def test_jsonl_envelopes_are_loaded_as_events_without_invented_genes(self) -> None:
        path = self.root / "runtime_exports" / "events.jsonl"
        path.write_text(json.dumps({
            "run_id": "r", "msg_id": "m", "msg_type": "signal",
            "sender": {"role": "planner", "instance": 0}, "receiver": "broadcast",
            "task_id": "t", "attempt": {"task_id": "t", "agent": {"role": "planner", "instance": 0}, "attempt": 0},
            "seq": 0, "ts": 1, "provenance": "live"
        }) + "\n", encoding="utf-8")
        dashboard = load_dashboard(path, self.root)
        self.assertEqual("live", dashboard.provenance)
        self.assertEqual(1, len(dashboard.events))
        self.assertEqual([], dashboard.genes)
        self.assertEqual([], dashboard.metrics)

    def test_t2_export_is_consumed_as_a_contract_local_jsonl_snapshot(self) -> None:
        event = Envelope(
            run_id="run-1", msg_id="msg-1", msg_type=MsgType.SIGNAL,
            sender=AgentId(role="planner", instance=0), receiver="broadcast", task_id="task-1",
            attempt=AttemptId(task_id="task-1", agent=AgentId(role="planner", instance=0), attempt=0),
            seq=0, ts=1.0, provenance="live",
        )

        class Store:
            def events(self, run_id: str) -> list[Envelope]:
                return [event] if run_id == "run-1" else []

        path = self.root / "runtime_exports" / "events.jsonl"
        self.assertEqual(1, export_events(cast(EventStore, Store()), "run-1", path))
        dashboard = load_dashboard(path, self.root)
        self.assertEqual("live", dashboard.provenance)
        self.assertEqual("not_run", dashboard.acceptance["task_live"])

    def test_rejects_paths_outside_allowlist(self) -> None:
        outside = self.root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(DashboardInputError, "demo/data"):
            load_dashboard(outside, self.root)

    def test_empty_state_never_claims_live_completion(self) -> None:
        dashboard = empty_dashboard()
        self.assertEqual("not_run", dashboard.acceptance["task_live"])
        self.assertIn("待发布", dashboard.hub_status)

    def test_typed_rehearsal_snapshot_is_consumed_without_local_contract_copy(self) -> None:
        agent = AgentId(role="builder", instance=0)
        snapshot = RehearsalSnapshot(
            sequence=0, stage="task_ready", at=1.0, task_id="task-rehearsal", task_description="fix known bug",
            provenance="live", acceptance=Acceptance(), checkpoints=None,
            members=[MemberAvailability(agent=agent, changed_at=1.0)],
            pipes=[PipeState(src=AgentId(role="planner", instance=0), dst=agent, weight=1.5, flow=1.0)],
            routing=RoutingFact(task_id="task-rehearsal", eligible_members=[agent]),
            tau_seconds=10.0, archive_threshold=0.2, model_calls_started=0,
        )
        document = RehearsalDocument(rehearsal_id="rehearsal-1", mode="live", current=snapshot, history=[snapshot])
        path = self.root / "runtime_exports" / "rehearsal.json"
        path.write_text(document.model_dump_json(), encoding="utf-8")
        dashboard = load_rehearsal(path)
        self.assertEqual("live", dashboard.provenance)
        self.assertEqual("task_ready", dashboard.rehearsal["current"]["stage"] if dashboard.rehearsal else None)
        self.assertEqual("固定彩排 rehearsal.json（现场快照）", dashboard.source_label)
        replay = load_rehearsal(path, replay=True)
        self.assertEqual("replay", replay.provenance)
        self.assertEqual("not_run", replay.acceptance["task_live"])
        self.assertEqual("固定彩排 rehearsal.json（回放视图）", replay.source_label)

    def test_rehearsal_requires_r_canonical_filename(self) -> None:
        other = self.root / "runtime_exports" / "other.json"
        other.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(DashboardInputError, "rehearsal.json"):
            load_rehearsal(other)

    def test_t2_runtime_sidecars_are_validated_without_payload_inference(self) -> None:
        root = self.root / "runtime_exports" / "run-1"
        root.mkdir()
        agent = AgentId(role="builder", instance=0)
        attempt = AttemptId(task_id="task-1", agent=agent, attempt=0)
        event = Envelope(run_id="run-1", msg_id="m", msg_type=MsgType.RESULT, sender=agent,
                         receiver="broadcast", task_id="task-1", attempt=attempt, seq=0, ts=1.0)
        result = TaskResult(run_id="run-1", task_id="task-1", attempt=attempt, status="succeeded",
                            artifact_uri="file:///evidence/sample.py",
                            verdict=Verification(passed=True, reviewer=AgentId(role="reviewer", instance=0),
                                                  evidence=["file:///evidence/review.txt"], exit_code=0),
                            acceptance=Acceptance(contract_local="passed", interface_live="passed", task_live="passed"))
        view = GeneView(ref=GeneRef(gene_id="verified", version=1), provenance="live", original_run_uri=None,
                        source_attempt=attempt, weight=1.0, use_count=1, injected_count=1, created_at=1.0,
                        last_used_at=1.0, evaluated_at=1.0, tau_seconds=60.0, archived_at=None)
        use = UseRecord(run_id="run-1", attempt=attempt, ref=view.ref, used_at=1.0, provenance="live")
        (root / "events.jsonl").write_text(event.model_dump_json() + "\n", encoding="utf-8")
        (root / "result.json").write_text(result.model_dump_json(), encoding="utf-8")
        (root / "genes.json").write_text(json.dumps([view.model_dump(mode="json")]), encoding="utf-8")
        (root / "adoption.json").write_text(json.dumps([use.model_dump(mode="json")]), encoding="utf-8")
        dashboard = load_runtime_export(root, self.root)
        self.assertEqual("passed", dashboard.acceptance["task_live"])
        self.assertEqual(1, len(dashboard.genes))
        self.assertEqual(1, len(dashboard.adoptions))

    def test_runtime_rejects_gene_snapshot_with_other_provenance(self) -> None:
        root = self.root / "runtime_exports" / "run-mixed"
        root.mkdir()
        agent = AgentId(role="builder", instance=0)
        attempt = AttemptId(task_id="task-mixed", agent=agent, attempt=0)
        event = Envelope(run_id="run-mixed", msg_id="m", msg_type=MsgType.RESULT, sender=agent,
                         receiver="broadcast", task_id="task-mixed", attempt=attempt, seq=0, ts=1.0)
        result = TaskResult(run_id="run-mixed", task_id="task-mixed", attempt=attempt, status="succeeded",
                            artifact_uri="file:///evidence/sample.py",
                            verdict=Verification(passed=True, reviewer=AgentId(role="reviewer", instance=0),
                                                  evidence=["file:///evidence/review.txt"], exit_code=0),
                            acceptance=Acceptance(interface_live="passed", task_live="passed"))
        mixed = GeneView(ref=GeneRef(gene_id="mock-gene"), provenance="mock", original_run_uri=None,
                         source_attempt=None, weight=1.0, use_count=0, injected_count=0, created_at=1.0,
                         last_used_at=None, evaluated_at=1.0, tau_seconds=60.0, archived_at=None)
        (root / "events.jsonl").write_text(event.model_dump_json() + "\n", encoding="utf-8")
        (root / "result.json").write_text(result.model_dump_json(), encoding="utf-8")
        (root / "genes.json").write_text(json.dumps([mixed.model_dump(mode="json")]), encoding="utf-8")
        (root / "adoption.json").write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(DashboardInputError, "genes.json 与 result.json"):
            load_runtime_export(root, self.root)

    def test_echarts_tooltips_use_rich_text_without_html_breaks(self) -> None:
        source = (Path(__file__).parents[2] / "viz" / "static" / "app.js").read_text(encoding="utf-8")
        self.assertEqual(4, source.count('renderMode: "richText"'))
        self.assertNotIn("<br>", source)
