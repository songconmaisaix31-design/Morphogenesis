from pathlib import Path
import subprocess

import pytest

from contracts.identity import AgentId, AttemptId
from local_assets import AssetApplicator, AssetPromoter, AssetSafetyError, AssetValidator, LocalAssetStore
from local_assets.models import SampleValidationPolicy
from local_assets.paths import git
from local_assets.snapshot import snapshot_revision
from swarm.code_patch import SamplePatch, candidate_from_patch


GOOD = '''def clamp(value, lower, upper):
    if lower > upper:
        raise ValueError("bounds")
    return max(lower, min(upper, value))

def mean(values):
    if not values:
        raise ValueError("empty")
    return sum(values) / len(values)

def unique(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result
'''
BAD = GOOD.replace("sum(values) / len(values)", "sum(values)")


@pytest.fixture
def fixed(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "sample.py").write_bytes(BAD.encode())
    git(repository, "init", "-b", "fixed-repair")
    git(repository, "add", "sample.py")
    git(repository, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-m", "seed")
    head = git(repository, "rev-parse", "HEAD").decode().strip()
    return repository, LocalAssetStore(tmp_path / "assets"), head


def candidate(head, source=GOOD, path="sample.py"):
    policy = SampleValidationPolicy(version="sample-tests-v1", path=path)
    patch = SamplePatch.model_validate({"changes": [{"path": path, "before": BAD, "after": source}]})
    return candidate_from_patch(patch, policy, attempt=AttemptId(
        task_id="code-task", agent=AgentId(role="builder", instance=0), attempt=0),
        scope=".", base_revision=head, base_head=head), policy


def test_fixed_code_accepts_semantics_without_gold_source(fixed):
    repository, store, head = fixed
    change, policy = candidate(head)
    revision, base_head = snapshot_revision(repository, ".", store.root / "snapshots")
    change = change.model_copy(update={"base_revision": revision, "base_head": base_head})
    assert "expectations" not in policy.model_dump()
    asset = store.publish(change)
    report = AssetValidator(store, repository, policy=policy).validate(asset)
    assert report.passed, report.reasons
    assert report.isolation == "fixed_pure_sample_subprocess"
    assert (repository / "sample.py").read_bytes() == BAD.encode()
    AssetPromoter(store, policy_version=policy.version).promote(asset, report.report_id)
    prepared = AssetApplicator(store, repository, policy_version=policy.version).prepare(asset, report.report_id)
    prepared.apply(lambda: None)
    assert (repository / "sample.py").read_bytes() == GOOD.encode()


def test_wrong_allowed_code_is_quarantined(fixed):
    repository, store, head = fixed
    change, policy = candidate(head, GOOD.replace("sum(values) / len(values)", "0"))
    asset = store.publish(change)
    report = AssetValidator(store, repository, policy=policy).validate(asset)
    assert not report.passed
    assert report.reasons == ("fixed_sample_acceptance_failed",)
    with pytest.raises(AssetSafetyError, match="report_not_passed"):
        AssetPromoter(store, policy_version=policy.version).promote(asset, report.report_id)
    assert (repository / "sample.py").read_bytes() == BAD.encode()


@pytest.mark.parametrize("source,path", [(GOOD + "\nimport os\n", "sample.py"),
    (GOOD.replace("return result", "return items.__class__"), "sample.py"),
    (GOOD, "tests.py"), (GOOD, "../sample.py")])
def test_patch_gate_refuses_capabilities_or_test_paths(source, path):
    with pytest.raises((AssetSafetyError, ValueError)):
        candidate("a" * 40, source, path)


def test_review_child_has_no_credentials_or_candidate_test_loading(fixed, monkeypatch):
    repository, store, head = fixed
    change, policy = candidate(head)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-secret-not-real")
    monkeypatch.setenv("PYTHONPATH", str(repository))
    run = subprocess.run
    children = []

    def checked(argv, **kwargs):
        if "-I" in argv:
            children.append(argv)
            assert "-S" in argv
            assert "DASHSCOPE_API_KEY" not in kwargs["env"]
            assert "PYTHONPATH" not in kwargs["env"]
            assert Path(argv[-2]).name == "acceptance_runner.py"
            assert not Path(argv[-2]).is_relative_to(repository)
        return run(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", checked)
    report = AssetValidator(store, repository, policy=policy).validate(store.publish(change))
    assert report.passed, report.reasons
    assert len(children) == 1


def test_arbitrary_commands_still_denied_for_sample(fixed):
    repository, store, head = fixed
    change, policy = candidate(head)
    report = AssetValidator(store, repository, policy=policy, commands=(("python", "sample.py"),)).validate(
        store.publish(change))
    assert not report.passed
    assert report.reasons == ("arbitrary_execution_isolation_unavailable",)
