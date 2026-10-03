"""Offline generated-candidate execution, security and admission; no live sandbox."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from orchestration.experiments.case import get_case
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor, read_generated_result
from orchestration.experiments.trusted import finalize_assessment
from tests.experiments.generated_helpers import (
    GENERATED_CODE, MockGeneratedBackend, approved_criteria_registry, code_sha256, make_context,
    make_poisson_plan, poisson_reference_output, poisson_wrong_output, verified_probe_registry,
)


def _execute(tmp_path, plan, *, output=None, entry_exit_code=0, timeout=False, probe_fail=False,
             probe_registry=None, run_id="gen-run-01"):
    backend = MockGeneratedBackend(tmp_path / "work", output=output, entry_exit_code=entry_exit_code,
                                   timeout=timeout, probe_fail=probe_fail)
    executor = GeneratedExperimentExecutor(backend, probe_registry=probe_registry)
    result = executor.execute(plan, make_context(run_id=run_id),
                              {"experiment.py": GENERATED_CODE.encode()}, tmp_path / "archive")
    return backend, result


def test_generated_candidate_is_not_registered_template():
    plan = make_poisson_plan()
    registered = get_case("nist-numacc4-v1").build_plan()
    assert plan.schema_version == "generated-experiment/v1"
    assert plan.entrypoint == "experiment.py"
    assert GENERATED_CODE.encode() != Path(registered.code.local_path).read_bytes()
    assert code_sha256() != registered.code.sha256


def test_generated_execute_supported_and_recompute(tmp_path):
    plan = make_poisson_plan()
    registry = verified_probe_registry()
    backend, result = _execute(tmp_path, plan, output=poisson_reference_output(100), probe_registry=registry)
    assert result.execution_state == "succeeded"
    assert result.assessment.execution == "succeeded"
    assert result.assessment.hypothesis == "supported"
    assert result.assessment.trusted is False
    assert result.assessment.mode == "diagnostic"
    assert result.assessment.metrics["max_absolute_error"] < 5e-3
    assert result.provenance == "mock" and result.usage is result.cost_usd is None
    assert backend.session.destroyed and backend.session.closed
    assert backend.create_calls == 1
    loaded = read_generated_result(tmp_path / "archive", "gen-run-01",
                                   expected_plan=result.plan, expected_context=result.context)
    assert loaded.assessment.hypothesis == "supported"
    assert loaded.assessment.metrics == result.assessment.metrics


def test_refuted_but_valid_output_is_not_failure(tmp_path):
    plan = make_poisson_plan()
    backend, result = _execute(tmp_path, plan, output=poisson_wrong_output(100),
                               probe_registry=verified_probe_registry())
    assert result.execution_state == "succeeded"
    assert result.assessment.execution == "succeeded"
    assert result.assessment.hypothesis == "refuted"
    assert result.assessment.contribution == "proposed"
    assert result.assessment.metrics["max_absolute_error"] > 0.1


@pytest.mark.parametrize("kwargs", [{"entry_exit_code": 2}, {"timeout": True}])
def test_crash_or_timeout_is_not_refutation(tmp_path, kwargs):
    plan = make_poisson_plan()
    backend, result = _execute(tmp_path, plan, probe_registry=verified_probe_registry(), **kwargs)
    assert result.execution_state in {"failed", "timeout"}
    assert result.assessment.hypothesis == "not_evaluated"
    assert result.assessment.execution == "failed"


def test_unverified_isolation_fails_closed(tmp_path):
    plan = make_poisson_plan()
    backend = MockGeneratedBackend(tmp_path / "work", output=poisson_reference_output(100))
    result = GeneratedExperimentExecutor(backend).execute(plan, make_context(),
                                                          {"experiment.py": GENERATED_CODE.encode()},
                                                          tmp_path / "archive")
    assert result.execution_state == "unsupported"
    assert backend.create_calls == 0


def test_mock_isolation_booleans_do_not_authorize_backend(tmp_path):
    plan = make_poisson_plan()
    backend = MockGeneratedBackend(tmp_path / "work", output=poisson_reference_output(100))
    result = GeneratedExperimentExecutor(backend).execute(plan, make_context(),
                                                          {"experiment.py": GENERATED_CODE.encode()},
                                                          tmp_path / "archive")
    assert backend.create_calls == 0
    assert result.execution_state == "unsupported"


def test_static_security_rejects_dangerous_code(tmp_path):
    dangerous = "import os\n" + GENERATED_CODE
    plan = make_poisson_plan(code=dangerous.encode())
    backend = MockGeneratedBackend(tmp_path / "work", output=poisson_reference_output(100))
    result = GeneratedExperimentExecutor(backend, probe_registry=verified_probe_registry()).execute(
        plan, make_context(), {"experiment.py": dangerous.encode()}, tmp_path / "archive")
    assert result.execution_state == "unsupported"
    assert backend.create_calls == 0
    assert any("danger" in reason for reason in result.admission.reasons)


def test_unapproved_dependency_rejected(tmp_path):
    code = "import pandas\n" + GENERATED_CODE
    plan = make_poisson_plan(code=code.encode())
    backend = MockGeneratedBackend(tmp_path / "work", output=poisson_reference_output(100))
    result = GeneratedExperimentExecutor(backend, probe_registry=verified_probe_registry()).execute(
        plan, make_context(), {"experiment.py": code.encode()}, tmp_path / "archive")
    assert result.execution_state == "unsupported"
    assert any("unapproved_dependency" in reason for reason in result.admission.reasons)
    assert backend.create_calls == 0


def test_self_reported_score_rejected(tmp_path):
    from tests.experiments.generated_helpers import poisson_scored_output
    plan = make_poisson_plan()
    backend, result = _execute(tmp_path, plan, output=poisson_scored_output(100),
                               probe_registry=verified_probe_registry())
    assert result.execution_state == "succeeded"
    assert result.assessment.hypothesis == "inconclusive"
    assert "output_schema_mismatch" in result.assessment.reasons


def test_finalize_requires_host_registry():
    plan = make_poisson_plan()
    diagnostic = finalize_assessment(
        _assessment("supported"), spec=plan.evaluation, registry=None,
        execution_state="succeeded", remote_effect="known")
    assert diagnostic.mode == "diagnostic"
    assert diagnostic.trusted is False
    final = finalize_assessment(
        _assessment("supported"), spec=plan.evaluation, registry=approved_criteria_registry(plan.evaluation),
        execution_state="succeeded", remote_effect="known")
    assert final.mode == "final"
    assert final.trusted is True
    unknown_effect = finalize_assessment(
        _assessment("supported"), spec=plan.evaluation, registry=approved_criteria_registry(plan.evaluation),
        execution_state="succeeded", remote_effect="unknown")
    assert unknown_effect.mode == "diagnostic"
    assert unknown_effect.trusted is False


def _assessment(hypothesis):
    from orchestration.experiments.generated import GeneratedAssessment
    return GeneratedAssessment(execution="succeeded", hypothesis=hypothesis, contribution="proposed",
                               mode="diagnostic", trusted=False)


def test_author_cannot_self_review():
    with pytest.raises(ValidationError, match="candidate_author_cannot_self_review"):
        make_context(author="same", reviewer="same")


def test_manifest_digest_mismatch_rejected(tmp_path):
    plan = make_poisson_plan()
    backend = MockGeneratedBackend(tmp_path / "work")
    with pytest.raises(ValueError, match="manifest_digest_mismatch"):
        GeneratedExperimentExecutor(backend).execute(plan, make_context(),
                                                     {"experiment.py": b"# different\n"},
                                                     tmp_path / "archive")
    assert backend.create_calls == 0


def test_read_generated_result_binding_tamper(tmp_path):
    plan = make_poisson_plan()
    backend, result = _execute(tmp_path, plan, output=poisson_reference_output(100),
                               probe_registry=verified_probe_registry())
    assert backend.create_calls == 1
    record = Path(result.archive_path) / "result.json"
    forged = json.loads(record.read_bytes())
    forged["assessment"]["metrics"] = {"forged": 999}
    record.write_text(json.dumps(forged))
    reloaded = read_generated_result(tmp_path / "archive", "gen-run-01")
    assert "forged" not in reloaded.assessment.metrics
    with pytest.raises(ValueError, match="expected_context_mismatch"):
        read_generated_result(tmp_path / "archive", "gen-run-01",
                              expected_context=make_context(run_id="gen-run-01").model_copy(update={"fencing_token": 2}))
