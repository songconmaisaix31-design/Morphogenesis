import json
import tempfile
import unittest
from pathlib import Path

from contracts.identity import AgentId, AttemptId
from contracts.messages import Envelope, MsgType
from orchestration.events import export_events
from viz.adapter import DashboardInputError, empty_dashboard, load_dashboard


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
        self.assertEqual(1, export_events(Store(), "run-1", path))
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
