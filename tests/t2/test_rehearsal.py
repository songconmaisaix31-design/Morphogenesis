"""Real subprocess verification and LangGraph; fixture proposals are mock only."""

import math
from pathlib import Path
import time

import pytest
from pydantic import ValidationError

from contracts.identity import AttemptId
from contracts.resolution import Gene
from contracts.results import TaskResult
from contracts.runtime import RunConfig
from orchestration.codex import CodexExecutor
from orchestration.rehearsal import Rehearsal, RehearsalOptions, read_rehearsal
from orchestration.rehearsal_models import RehearsalDocument, RehearsalSnapshot, Stage
from tests.t2.test_codex import fake_cli


class FixtureExecutor:
    def __init__(self, evidence: Path, attempts: list[AttemptId], *, missing_usage: bool = False,
                 broken: bool = False, adopt: bool = True) -> None:
        self.evidence, self.attempts = evidence, attempts
        self.missing_usage, self.broken, self.adopt = missing_usage, broken, adopt

    def execute(self, attempt: AttemptId, config: RunConfig, genes: list[Gene]) -> TaskResult:
        self.attempts.append(attempt)
        fixture = self.evidence.parent / "fixture"
        fixture.mkdir()
        command = fake_cli(fixture, adopted=[gene.ref.gene_id for gene in genes] if self.adopt else [])
        if self.broken:
            command = fake_cli(fixture, content=(Path(config.workspace) / "sample.py").read_text())
        if self.missing_usage:
            script = fixture / "fake_cli.py"
            script.write_text(script.read_text().replace("turn.completed", "no_usage"))
        return CodexExecutor(self.evidence, model="fixture", command=command, provenance="mock").execute(
            attempt, config, genes)


def options(tmp_path: Path, **changes: object) -> RehearsalOptions:
    return RehearsalOptions.model_validate({"root": tmp_path / "run", "stage_delay": 0,
                                            "tau_seconds": 0.1, "tick_seconds": 0.025, **changes})


@pytest.mark.parametrize("adoption_snapshot_delay", [0.0, 0.2], ids=["normal", "slow-adoption-snapshot"])
def test_complete_rehearsal_routes_actual_second_execution_and_metabolizes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, adoption_snapshot_delay: float,
) -> None:
    attempts: list[AttemptId] = []
    seen: list[RehearsalDocument] = []
    entered: list[str] = []

    def offline(prompt: str) -> str:
        assert len(attempts) == 1
        assert seen[-1].current.stage == "awaiting_offline"
        assert all(member.available for member in seen[-1].current.members)
        entered.append(prompt)
        return ""

    app = Rehearsal(options(tmp_path, mode="manual"), provenance="mock",
                    executor_factory=lambda evidence, _: FixtureExecutor(evidence, attempts),
                    on_snapshot=seen.append, wait_for_offline=offline)
    emit = app._emit

    def delayed_emit(stage: Stage, message: str = "", failure: str | None = None) -> RehearsalDocument:
        if stage == "gene_adopted":
            # Delay observation AFTER mark_used, without faking either clock.
            # With tau=0.1, 0.2 seconds also exercises decay past the old >0.5 assertion.
            time.sleep(adoption_snapshot_delay)
        return emit(stage, message, failure)

    monkeypatch.setattr(app, "_emit", delayed_emit)
    original_topology = app.topology.snapshot()
    started = time.time()
    document = app.run()
    assert document.current.stage == "completed", document.current.failure
    assert len(attempts) == 2 and len(entered) == 1
    assert attempts[0].task_id != attempts[1].task_id
    assert attempts[0].agent != attempts[1].agent
    assert document.current.routing.selected_attempt == attempts[1]
    assert document.current.routing.removed_member == attempts[0].agent
    assert document.current.routing.eligible_members == [attempts[1].agent]
    assert all(pipe.active for pipe in app.topology.snapshot())  # No policy pollution.
    assert next(pipe for pipe in document.current.pipes if pipe.dst == attempts[0].agent).active is False
    after_feedback = next(s for s in document.history if s.stage == "gene_generated")
    assert after_feedback.pipes[0].weight > original_topology[0].weight
    assert document.history[0].checkpoints is not None
    assert document.history[0].checkpoints.passed_count == 0
    assert document.current.checkpoints is not None
    assert document.current.checkpoints.passed_count == 3
    assert len(document.current.genes) == 2
    assert {gene.source_attempt for gene in document.current.genes} == set(attempts)
    adopted = next(s for s in document.history if s.stage == "gene_adopted")
    adoption = next(record for record in adopted.adoptions if record.attempt == attempts[1])
    adopted_gene = next(gene for gene in adopted.genes if gene.ref == adoption.ref)
    assert adopted_gene.source_attempt == attempts[0]
    assert adopted_gene.use_count == 1
    assert adopted_gene.last_used_at is not None
    assert adopted_gene.last_used_at == adoption.used_at
    assert adopted_gene.created_at < adopted_gene.last_used_at <= adopted_gene.evaluated_at
    assert adopted_gene.tau_seconds == app.options.tau_seconds
    # Refresh anchors at adoption, not at the later snapshot; arbitrary elapsed
    # wall time is valid, including a slow observer that sees weight below 0.5.
    elapsed = adopted_gene.evaluated_at - adopted_gene.last_used_at
    assert adopted_gene.weight == pytest.approx(math.exp(-elapsed / adopted_gene.tau_seconds))
    assert document.current.retrievable_gene_ids == []
    assert all(gene.archived_at is not None for gene in document.current.genes)
    assert all(started <= s.at <= time.time() for s in document.history)
    assert document.current.model_calls_started == 2
    assert document.current.cost_usd is None
    assert all(s.acceptance.interface_live == s.acceptance.task_live == "not_run" for s in document.history)
    assert read_rehearsal(app.root / "rehearsal.json") == document
    artifacts = {path: (path.stat().st_mtime_ns, path.stat().st_size) for path in app.root.rglob("*") if path.is_file()}
    replay = read_rehearsal(app.root / "rehearsal.json", replay=True)
    assert replay.mode == "replay"
    assert replay.original_run_uri == (app.root / "rehearsal.json").as_uri()
    assert all(s.provenance == "replay" and s.acceptance.task_live == "not_run" for s in replay.history)
    assert all(g.provenance == "replay" for g in replay.current.genes)
    assert all(r.provenance == "replay" for r in replay.current.results)
    assert all(u.provenance == "replay" for u in replay.current.adoptions)
    assert artifacts == {path: (path.stat().st_mtime_ns, path.stat().st_size) for path in artifacts}
    with pytest.raises(ValueError, match="empty root"):
        Rehearsal(options(tmp_path), provenance="mock", executor_factory=lambda p, _: FixtureExecutor(p, attempts))
    assert len(attempts) == 2
    invalid = document.current.model_dump()
    invalid["provenance"] = "live"
    with pytest.raises(ValidationError, match="matching provenance"):
        RehearsalSnapshot.model_validate(invalid)


@pytest.mark.parametrize("failure", ["unknown_tokens", "failed_verification", "unknown_execution"])
def test_failure_or_unknown_never_starts_second_task_or_retries(tmp_path: Path, failure: str) -> None:
    attempts: list[AttemptId] = []

    class UnknownExecutor(FixtureExecutor):
        def execute(self, attempt: AttemptId, config: RunConfig, genes: list[Gene]) -> TaskResult:
            self.attempts.append(attempt)
            raise RuntimeError("UNKNOWN external outcome")

    app = Rehearsal(options(tmp_path), provenance="mock", executor_factory=lambda evidence, _: (
        UnknownExecutor(evidence, attempts) if failure == "unknown_execution" else FixtureExecutor(
            evidence, attempts, missing_usage=failure == "unknown_tokens", broken=failure == "failed_verification")))
    document = app.run()
    assert document.current.stage == "failed"
    assert len(attempts) == document.current.model_calls_started == 1
    assert not (app.root / "recovery").exists()
    assert read_rehearsal(app.root / "rehearsal.json").current.failure
    assert document.current.acceptance.task_live == "not_run"


def test_injection_without_explicit_adoption_does_not_complete(tmp_path: Path) -> None:
    attempts: list[AttemptId] = []
    app = Rehearsal(options(tmp_path), provenance="mock", executor_factory=lambda evidence, _: FixtureExecutor(
        evidence, attempts, adopt=False))
    document = app.run()
    assert document.current.stage == "failed"
    assert "no actual adoption" in (document.current.failure or "")
    assert len(attempts) == 2
    assert document.current.adoptions == []
    assert len(document.current.genes) == 2


def test_live_requires_two_explicit_new_task_authorizations_before_effects(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authorization"):
        Rehearsal(options(tmp_path))
    assert not (tmp_path / "run").exists()
