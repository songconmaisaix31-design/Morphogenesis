"""Generated candidate boundary using inert bytes and host-created output only.

No imports from tests/experiments/generated_helpers.py; no candidate is run.
"""
import hashlib
import json
import math

import pytest

from orchestration.experiments.evaluation import evaluate
from orchestration.experiments.generated import (
    ApprovedEnvironment, EvaluationSpec, GeneratedAssessment, GeneratedContext,
    GeneratedExperimentPlan, GeneratedFile, GeneratedResult, GeneratedSource,
    IsolationCapability, IsolationReport,
)
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor, read_generated_result
from orchestration.experiments.models import ExperimentArtifact


CODE = b"# inert candidate, never executed by Q\n"


def plan(**updates):
    p = GeneratedExperimentPlan(
        plan_id="q-plan", project_id="p1", branch_id="b1", task_id="t1",
        candidate_asset_id="candidate", candidate_revision="a" * 40,
        authorization_ref="proposed-authority",
        files=(GeneratedFile(name="candidate.py", sha256=hashlib.sha256(CODE).hexdigest(),
                             size_bytes=len(CODE), source="fixture"),), entrypoint="candidate.py",
        environment=ApprovedEnvironment(image="fixture:1", dependency_lock_sha256="b" * 64),
        evaluation=EvaluationSpec(version="q-eval", kind="poisson_reference_v1", n_intervals=4),
        sources=(GeneratedSource(kind="hypothesis", ref="fixture"),),
        claim="fixture claim", hypothesis="fixture hypothesis")
    return p.model_copy(update=updates)


def context():
    return GeneratedContext(run_id="q-run", task_id="t1", worker_id="q", fencing_token=1,
                            author="candidate-author", reviewer="caller-invented-reviewer")


def isolation(verified=False):
    capability = IsolationCapability(**{key: True for key in IsolationCapability.model_fields})
    return IsolationReport(backend="caller-declared", declared=capability,
                           verified=verified, probe="passed" if verified else "not_run")


class NoRunBackend:
    provenance = "mock"
    capabilities = frozenset({"script", "cpu", "memory", "duration"})

    def __init__(self, verified=False):
        self.verified = verified
        self.create_calls = 0

    def isolation(self):
        return isolation(self.verified)

    def create(self, *args, **kwargs):
        self.create_calls += 1
        raise AssertionError("Q backend sentinel: candidate must never reach create")


def raw_output():
    xs = [i / 4 for i in range(5)]
    return json.dumps({"x": xs, "u": [math.sin(math.pi * x) for x in xs]}).encode()


def archive(root, p=None, *, bind_artifacts=False, **updates):
    p = p or plan()
    directory = root / "q-run"
    (directory / "inputs").mkdir(parents=True)
    (directory / "outputs").mkdir()
    (directory / "inputs/candidate.py").write_bytes(CODE)
    (directory / "outputs/output.json").write_bytes(raw_output())
    result = GeneratedResult(plan=p, context=context(), archive_path=str(directory), provenance="mock",
                             isolation=isolation(), execution_state="succeeded", remote_effect="known")
    if bind_artifacts:
        entries = []
        for name in ("inputs/candidate.py", "outputs/output.json"):
            raw = (directory / name).read_bytes()
            entries.append(ExperimentArtifact(name=name, archive_path=name,
                            sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)))
        result = result.model_copy(update={"artifacts": tuple(entries)})
    result = result.model_copy(update=updates)
    (directory / "plan.json").write_text(p.model_dump_json(), encoding="utf-8")
    (directory / "result.json").write_text(result.model_dump_json(), encoding="utf-8")
    return directory, result


def test_unverified_isolation_never_reaches_backend(tmp_path):
    backend = NoRunBackend()
    result = GeneratedExperimentExecutor(backend).execute(plan(), context(), {"candidate.py": CODE}, tmp_path)
    assert backend.create_calls == 0
    assert result.execution_state == "unsupported"
    assert not result.assessment.trusted
    assert result.assessment.hypothesis == "not_evaluated"


def test_mock_isolation_booleans_do_not_authorize_backend(tmp_path):
    backend = NoRunBackend(verified=True)
    result = GeneratedExperimentExecutor(backend).execute(plan(), context(), {"candidate.py": CODE}, tmp_path)
    assert backend.create_calls == 0, "caller/mock booleans allowed execution admission"
    assert result.execution_state == "unsupported"


def test_caller_approved_and_reviewer_boolean_cannot_grant_final_assessment():
    p = plan(evaluation=EvaluationSpec(version="forged-approval", kind="poisson_reference_v1",
                                     n_intervals=4, approved=True, approved_by="invented"))
    assessment = evaluate(p, raw_output(), reviewer_independent=True)
    assert assessment.mode == "diagnostic", "untrusted approval/reviewer booleans granted final science"
    assert assessment.contribution != "accepted"


@pytest.mark.parametrize("field", ["evaluation", "environment", "data_refs", "authorization_ref"])
def test_archive_whole_plan_binding_rejects_change(tmp_path, field):
    original = plan()
    changed = {
        "evaluation": original.evaluation.model_copy(update={"max_abs_tolerance": 0.5}),
        "environment": original.environment.model_copy(update={"dependency_lock_sha256": "c" * 64}),
        "data_refs": ("changed-data",),
        "authorization_ref": "changed-authority",
    }[field]
    archive(tmp_path, original.model_copy(update={field: changed}))
    with pytest.raises(ValueError):
        read_generated_result(tmp_path, "q-run", expected_plan=original, expected_context=context())


def test_candidate_self_score_not_trusted():
    output = json.loads(raw_output())
    output.update(score=1.0, passed=True)
    result = evaluate(plan(), json.dumps(output).encode(), reviewer_independent=True)
    assert result.hypothesis == "inconclusive"
    assert result.mode == "diagnostic"
    assert result.contribution != "accepted"


@pytest.mark.parametrize("state", ["unknown", "failed", "timeout"])
def test_archive_unknown_crash_timeout_cannot_retain_forged_reward(tmp_path, state):
    archive(tmp_path, execution_state=state, remote_effect="unknown",
            assessment=GeneratedAssessment(execution="succeeded", hypothesis="supported",
                                           contribution="accepted", mode="final", trusted=True))
    try:
        result = read_generated_result(tmp_path, "q-run", expected_plan=plan(), expected_context=context())
    except ValueError:
        return
    assert not result.assessment.trusted
    assert result.assessment.hypothesis not in {"supported", "refuted"}
    assert result.assessment.contribution != "accepted"


def test_known_execution_with_unknown_effect_cannot_grant_final(tmp_path):
    p = plan(evaluation=EvaluationSpec(version="forged", kind="poisson_reference_v1", n_intervals=4,
                                     approved=True, approved_by="invented"))
    archive(tmp_path, p, bind_artifacts=True, remote_effect="unknown", cleanup_state="unknown")
    try:
        result = read_generated_result(tmp_path, "q-run", expected_plan=p, expected_context=context())
    except ValueError:
        return
    assert result.assessment.mode == "diagnostic"
    assert result.assessment.contribution != "accepted"


def test_succeeded_archive_requires_output_digest_binding(tmp_path):
    archive(tmp_path)
    with pytest.raises(ValueError):
        read_generated_result(tmp_path, "q-run", expected_plan=plan(), expected_context=context())


def test_bound_archive_recomputes_diagnostic_without_caller_reward(tmp_path):
    archive(tmp_path, bind_artifacts=True,
            assessment=GeneratedAssessment(execution="succeeded", hypothesis="refuted",
                contribution="accepted", mode="final", trusted=True, metrics={"self_score": 1}))
    result = read_generated_result(tmp_path, "q-run", expected_plan=plan(), expected_context=context())
    assert result.assessment.mode == "diagnostic"
    assert result.assessment.hypothesis == "supported"
    assert result.assessment.contribution == "proposed"
    assert "self_score" not in result.assessment.metrics
