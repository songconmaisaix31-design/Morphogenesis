"""Two cases through the same offline executor; no live sandbox or model."""

from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestration.experiments.case import get_case, public_case
from orchestration.experiments.executor import ExperimentExecutor, read_result
from orchestration.experiments.models import ExperimentPlan
from orchestration.experiments.scientific import assess
from tests.experiments.test_execution import CASE, LocalContractBackend, context


IDS = ("nist-numacc4-v1", "synthetic-linear-regression-v1")


@pytest.mark.parametrize("case_id", IDS)
def test_registered_case_same_executor_and_durable_recalculation(tmp_path, case_id):
    definition = get_case(case_id)
    plan = definition.build_plan()
    assert plan.criteria.version == definition.case_id and plan.claim == definition.claim
    backend = LocalContractBackend(tmp_path / "work")
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.execution_state == "succeeded" and result.scientific.verdict == "passed"
    assert result.scientific.criteria_version == case_id
    assert backend.create_calls == 1 and backend.session.destroyed and backend.session.closed
    assert result.provenance == "mock" and result.usage is result.cost_usd is None
    assert read_result(tmp_path / "archive", context().run_id, expected_plan=plan, expected_context=context()) == result
    record = Path(result.archive_path) / "result.json"
    forged = json.loads(record.read_bytes())
    forged["scientific"]["metrics"] = {"forged": 999}
    record.write_text(json.dumps(forged))
    assert "forged" not in read_result(tmp_path / "archive", context().run_id).scientific.metrics


def test_old_default_plan_and_metadata_compatibility():
    definition = get_case(IDS[0])
    plan = public_case(CASE, order="reverse")
    assert plan == definition.build_plan(directory=CASE, order="reverse")
    assert definition.problem == "Reproduce NIST NumAcc4 sample variance using CPython statistics.variance."
    assert definition.template_summary == "NIST NumAcc4 variance method; predeclared conditions only"
    assert definition.file_policy_prefix == "nist"
    legacy = plan.model_dump(mode="json")
    del legacy["criteria"]["version"]
    assert ExperimentPlan.model_validate(legacy) == plan
    with pytest.raises(FrozenInstanceError):
        definition.title = "changed"


@pytest.mark.parametrize("case_id", IDS)
@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_archive_input_identity_survives_checkout_line_endings(tmp_path, case_id, newline):
    plan = get_case(case_id).build_plan()
    code = Path(plan.code.local_path).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", newline)
    path = tmp_path / plan.code.name
    path.write_bytes(code)
    plan = plan.model_copy(update={"code": plan.code.model_copy(update={
        "local_path": str(path), "sha256": hashlib.sha256(code).hexdigest()})})
    backend = LocalContractBackend(tmp_path / "work")
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.scientific.verdict == "passed"
    assert read_result(tmp_path / "archive", context().run_id, expected_plan=plan) == result


def test_unknown_case_and_criteria_fail_before_backend(tmp_path):
    backend = LocalContractBackend(tmp_path / "work")
    with pytest.raises(ValueError, match="unknown_registered_case"):
        get_case("user.validator:shell")
    value = get_case(IDS[1]).build_plan().model_dump(mode="json")
    for criteria in ({"version": "unknown"}, {"version": IDS[1], "sse_absolute_tolerance": 1},
                     {"version": IDS[1], "validator": "python -c pass"}):
        value["criteria"] = criteria
        with pytest.raises(ValidationError):
            ExperimentPlan.model_validate(value)
    assert backend.create_calls == 0
    with pytest.raises(ValueError, match="unsupported_case_order"):
        get_case(IDS[1]).build_plan(order="reverse")


def test_direct_trusted_judge_revalidates_policy_not_model_copy_bypass():
    definition = get_case(IDS[1])
    plan = definition.build_plan()
    plan = plan.model_copy(update={"criteria": plan.criteria.model_copy(update={"sse_absolute_tolerance": 1})})
    with pytest.raises(ValidationError):
        definition.assess(plan, Path(plan.data.local_path).read_bytes(), b"{}")


@pytest.mark.parametrize("case_id", IDS)
@pytest.mark.parametrize("label", ["code", "data"])
def test_other_code_or_data_rejected_even_with_matching_plan_digest(tmp_path, case_id, label):
    plan = get_case(case_id).build_plan()
    item = getattr(plan, label)
    changed = Path(item.local_path).read_bytes() + b"\n# changed\n"
    path = tmp_path / item.name
    path.write_bytes(changed)
    item = item.model_copy(update={"local_path": str(path), "sha256": hashlib.sha256(changed).hexdigest()})
    plan = plan.model_copy(update={label: item})
    backend = LocalContractBackend(tmp_path / "work")
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.execution_state == "failed" and result.cleanup_state == "not_created"
    assert result.scientific.verdict == "not_evaluated" and backend.create_calls == 0


@pytest.mark.parametrize("mode,state", [("failed", "failed"), ("timeout", "timeout"),
    ("unknown", "unknown"), ("missing", "missing_artifact"), ("transport_timeout", "unknown")])
def test_second_case_preserves_execution_failure_semantics(tmp_path, mode, state):
    plan = get_case(IDS[1]).build_plan()
    backend = LocalContractBackend(tmp_path / "work", mode)
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.execution_state == state and result.scientific.verdict == "not_evaluated"
    assert result.scientific.criteria_version == IDS[1] and backend.create_calls == 1
    assert read_result(tmp_path / "archive", context().run_id).scientific.verdict == "not_evaluated"
    assert result.cost_usd is result.usage is None


@pytest.mark.parametrize("mutation", ["bool", "nonfinite", "missing", "residual", "slope", "intercept", "sse", "summary"])
def test_independent_linear_judge_rejects_real_negative_values(mutation):
    plan = get_case(IDS[1]).build_plan()
    raw = Path(plan.data.local_path).read_bytes()
    output = {"count": 7, "slope": 1.5, "intercept": 2, "sse": 0.25,
              "residuals": [0.25, -0.25, 0, 0, 0, -0.25, 0.25]}
    assert assess(plan, raw, json.dumps(output).encode()).verdict == "passed"
    if mutation == "bool":
        output["slope"] = True
    elif mutation == "nonfinite":
        output["residuals"][0] = float("inf")
    elif mutation == "missing":
        del output["residuals"]
    elif mutation == "residual":
        output["residuals"] = [0] * 7
    elif mutation == "summary":
        output["passed"] = True
    else:
        output[mutation] += 0.1
    judged = assess(plan, raw, json.dumps(output).encode())
    assert judged.verdict == "failed" and judged.criteria_version == IDS[1]


def test_original_notebook_registered_before_optional_capability_check(tmp_path):
    plan = public_case(CASE)
    raw = (CASE / "experiment.ipynb").read_bytes()
    plan = plan.model_copy(update={"mode": "notebook", "code": plan.code.model_copy(update={
        "name": "experiment.ipynb", "local_path": str(CASE / "experiment.ipynb"),
        "sha256": hashlib.sha256(raw).hexdigest()})})
    backend = LocalContractBackend(tmp_path / "work")
    result = ExperimentExecutor(backend).execute(plan, context(), tmp_path / "archive")
    assert result.execution_state == "unsupported" and backend.create_calls == 0
    assert result.reasons == ("notebook",)
