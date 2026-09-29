"""Bounded Owner evidence; reuses the 2026-09-28 independent 12-case matrix.

Source: morph-fc-acceptance-0928-final/.runtime/acceptance-0928/validate_schema.py,
report at 4409a60e278ce328fd76588d680e3c4438bdaa84 (repository Apache-2.0).
Uses installed jsonschema (MIT) and Pydantic (MIT); no production consumer added.
"""
import argparse
import copy
import importlib.metadata
import json
import re
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
BASE = "73798cd6f05210f2bd9b1eebfd6f9f0dd6e842db"
FC = "73e64cc70116ac658d85591d082c0684a4952c99"
SCHEMA_PATH = "docs/FC_LOG_SCHEMA_DRAFT_0928.md"


def blob(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def extract(raw):
    blocks = re.findall(r"```json\s*\n(.*?)\n```", raw.decode("utf-8"), re.S)
    assert len(blocks) == 1
    return json.loads(blocks[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", required=True, help="Immutable SHA or WORKTREE")
    parser.add_argument("--production-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = (ROOT / SCHEMA_PATH).read_bytes() if args.revision == "WORKTREE" else blob(args.revision, SCHEMA_PATH)
    schema, baseline = extract(raw), extract(blob(BASE, SCHEMA_PATH))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    expected = copy.deepcopy(baseline)
    del expected["allOf"][1]["then"]["required"]
    assert schema in (baseline, expected), "Schema changed beyond one nullable required removal"

    # Read an immutable extraction; verify every imported local module's Git blob.
    production = args.production_root.resolve()
    sys.path.insert(0, str(production))
    from swarm.fault_observations import FaultObservation
    verified_sources = []
    for module in list(sys.modules.values()):
        file = getattr(module, "__file__", None)
        if file and Path(file).is_relative_to(production) and Path(file).suffix == ".py":
            relative = Path(file).relative_to(production).as_posix()
            assert Path(file).read_bytes() == blob(FC, relative), relative
            verified_sources.append(relative)
    assert len(FaultObservation.model_fields) == 14
    assert schema["$defs"]["FaultObservation"] == FaultObservation.model_json_schema()
    count, audit = "audit_confirmed_issue_events", "issue_audit"
    for field in (count, audit):
        assert field not in schema["required"]
        assert "default" not in schema["properties"][field]

    # Original independently validated event wrapper and twelve cases, kept intact.
    base = {
        "schema_version": "1.0.0", "run_id": "test-run-123", "sequence": 1,
        "task_id": "task-456", "at": 1634567890, "duration_seconds": 5.5,
        "drill": False, "provenance": "live", "evidence_label": "LIVE",
        "original_run_uri": None, "event": "fault_observation", "dag_node": None,
        "asset_calls": [], "routing": None, "claim": None, "rehearsal": None,
        "fault_observation": {
            "observation_id": "obs-789", "run_id": "test-run-123", "task_id": "task-456",
            "request_id": "req-101", "attempt": 0, "provider": "test-provider",
            "model": "test-model", "failure_class": "confirmed_rejection",
            "normalized_reason": "test reason", "occurred_at": 1634567890,
        },
    }
    validator.validate(base)
    evidence = {"status": "complete", "protocol_id": "test-protocol", "scope": "test-scope",
                "reviewer": "test-reviewer", "confirmed_issue_ids": [], "evidence_refs": ["evidence-1"]}
    partial = {**evidence, "status": "partial"}
    positive = {**evidence, "confirmed_issue_ids": ["issue-1"]}
    cases = [
        ("01_both_missing", {}, True),
        ("02_both_null", {count: None, audit: None}, True),
        ("03_only_count_null", {count: None}, True),
        ("04_only_audit_null", {audit: None}, True),
        ("05_zero_complete", {count: 0, audit: evidence}, True),
        ("06_zero_partial", {count: 0, audit: partial}, False),
        ("07_negative_complete", {count: -1, audit: evidence}, False),
        ("08_integer_no_audit", {count: 1}, False),
        ("09_audit_no_count", {audit: evidence}, False),
        ("10_integer_null_audit", {count: 1, audit: None}, False),
        ("11_null_count_object_audit", {count: None, audit: evidence}, False),
        ("12_positive_partial", {count: 1, audit: {**partial, "confirmed_issue_ids": ["issue-1"]}}, True),
        ("13_positive_complete", {count: 1, audit: positive}, True),
        ("14_positive_without_evidence", {count: 1, audit: {**positive, "evidence_refs": []}}, False),
        ("15_zero_no_audit", {count: 0}, False),
        ("16_zero_null_audit", {count: 0, audit: None}, False),
        ("17_zero_nonempty_ids", {count: 0, audit: positive}, False),
        ("18_fractional_count", {count: 0.5, audit: positive}, False),
        ("19_boolean_count", {count: True, audit: positive}, False),
        ("20_string_count", {count: "1", audit: positive}, False),
        ("21_empty_audit", {count: 1, audit: {}}, False),
        ("22_duplicate_issue_ids", {count: 2, audit: {**positive, "confirmed_issue_ids": ["issue-1", "issue-1"]}}, False),
        ("23_unknown_audit_property", {count: 1, audit: {**positive, "invented": True}}, False),
        ("24_orphan_partial_audit", {audit: {**partial, "confirmed_issue_ids": ["issue-1"]}}, False),
    ]
    controls = [
        ("live_as_SIMULATED", {"evidence_label": "SIMULATED"}, False),
        ("drill_with_live", {"drill": True}, False),
        ("mock_drill_valid", {"drill": True, "provenance": "mock", "evidence_label": "SIMULATED"}, True),
        ("replay_missing_uri", {"provenance": "replay", "evidence_label": "REPLAY"}, False),
        ("replay_valid", {"provenance": "replay", "evidence_label": "REPLAY", "original_run_uri": "run://source"}, True),
        ("event_payload_null", {"fault_observation": None}, False),
        ("task_id_null", {"task_id": None}, False),
        ("unknown_field", {"invented": True}, False),
        ("zero_without_evidence", {count: 0, audit: {**evidence, "evidence_refs": []}}, False),
        ("negative_duration", {"duration_seconds": -1}, False),
        ("negative_fault_attempt", {"fault_observation": {**base["fault_observation"], "attempt": -1}}, False),
        ("invalid_cost_state", {"fault_observation": {**base["fault_observation"], "cost_state": "free"}}, False),
        ("explicit_unknown_fault_fields", {"fault_observation": {**base["fault_observation"], "cost_state": None,
                                                               "retry_after_seconds": None, "switched_to": None, "evidence_ref": None}}, True),
    ]

    def run_matrix(matrix):
        results = []
        for name, changes, expected_valid in matrix:
            payload = copy.deepcopy(base)
            payload.update(copy.deepcopy(changes))
            before = copy.deepcopy(payload)
            errors = list(validator.iter_errors(payload))
            assert payload == before, "validation filled missing or null input"
            actual = not errors
            row = {"case": name, "expected_valid": expected_valid, "actual_valid": actual,
                   "passed": actual == expected_valid,
                   "errors": [{"message": e.message, "path": list(e.absolute_path),
                               "schema_path": list(e.absolute_schema_path)} for e in errors]}
            results.append(row)
            print(name, "VALID" if actual else "INVALID", "PASS" if row["passed"] else "FAIL")
        return results

    results, control_results = run_matrix(cases), run_matrix(controls)
    # Existing documented consumer obligation, deliberately NOT a production validator.
    # Draft 2020-12 does not compare an arbitrary integer to an array's length.
    limitations = []
    for name, n, ids in (("positive_empty_ids", 1, []), ("positive_count_mismatch", 2, ["issue-1"])):
        payload = {**base, count: n, audit: {**evidence, "confirmed_issue_ids": ids}}
        actual = validator.is_valid(payload)
        assert actual, "documented cross-field limitation changed"
        assert n != len(set(ids))
        limitations.append({"case": name, "schema_valid": actual, "consumer_count_equals_unique_ids": False,
                            "production_consumer": "NOT_IMPLEMENTED"})
        print("LIMITATION", name, "Schema VALID; consumer must reject, NOT_IMPLEMENTED")

    original_passed = sum(x["passed"] for x in results[:12])
    passed = sum(x["passed"] for x in results)
    controls_passed = sum(x["passed"] for x in control_results)
    success = all(x["passed"] for x in results + control_results)
    output = {"schema_revision": args.revision, "baseline": BASE, "fault_source_sha": FC,
              "verified_imported_sources": sorted(verified_sources),
              "python": sys.version, "jsonschema": importlib.metadata.version("jsonschema"),
              "pydantic": importlib.metadata.version("pydantic"),
              "schema_diff": "unchanged" if schema == baseline else "only allOf/1/then/required removed",
              "fault_observation_14_export_exact": True, "non_audit_unchanged": True,
              "optional_no_default_input_unchanged": True,
              "original_matrix": f"{original_passed}/12", "expanded_matrix": f"{passed}/{len(results)}",
              "controls_summary": f"{controls_passed}/{len(controls)}", "exit_code": 0 if success else 1,
              "cases": results, "controls": control_results, "documented_limitations": limitations}
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RESULT original={original_passed}/12 expanded={passed}/{len(results)} controls={controls_passed}/{len(controls)} exit={output['exit_code']}")
    return output["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
