from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts import (
    Acceptance, AgentId, AttemptId, Envelope, Gene, GeneRef, MsgType,
    Provision, RunConfig, TaskResult, Usage, Verification,
)
from contracts.protocols import EventStore, GeneStore, ResultStore
from persistence import SQLiteStore


BUILDER = AgentId(role="builder", instance=0)
REVIEWER = AgentId(role="reviewer", instance=0)
ATTEMPT = AttemptId(task_id="repair", agent=BUILDER, attempt=0)


def event(run: str = "run-a", msg_id: str = "m1", seq: int = 1) -> Envelope:
    return Envelope(
        run_id=run, msg_id=msg_id, msg_type=MsgType.RESULT,
        sender=BUILDER, receiver=REVIEWER, task_id="repair", attempt=ATTEMPT,
        seq=seq, ts=1.0,
    )


def test_caller_and_sqlite_implementation_roundtrip(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "metadata.db")
    caller: EventStore = store
    assert caller.append_event(event())
    assert not caller.append_event(event())
    caller.mark_handled("run-a", "m1")
    assert not caller.append_event(event())
    assert caller.append_event(event(msg_id="m0", seq=0))
    assert caller.append_event(event(run="run-b"))
    store.close()
    reopened = SQLiteStore(tmp_path / "metadata.db")
    rows = reopened.events("run-a")
    assert [row.msg_id for row in rows] == ["m0", "m1"]
    assert rows[1].handled
    assert len(reopened.events("run-b")) == 1
    with pytest.raises(ValueError, match="different event"):
        reopened.append_event(event().model_copy(update={"seq": 99}))
    with pytest.raises(KeyError):
        reopened.mark_handled("run-a", "not-found")
    reopened.close()


def test_results_and_genes_persist_using_their_protocols(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "metadata.db")
    results: ResultStore = store
    local_pass = Verification(
        passed=True, reviewer=REVIEWER, evidence=["file:///independent.txt"], exit_code=0
    )
    result = TaskResult(
        run_id="run-a", task_id="repair", attempt=ATTEMPT, status="succeeded",
        verdict=local_pass, artifact_uri="file:///sample.py",
        acceptance=Acceptance(contract_local="passed"),
    )
    results.save_result(result)
    assert results.get_result("run-a", ATTEMPT) == result
    assert results.get_result("run-b", ATTEMPT) is None
    assert result.acceptance.task_live == "not_run"
    genes: GeneStore = store
    ref = GeneRef(gene_id="bounds", asset_id="official-sdk-owned-id")
    gene = Gene(ref=ref, signals_match=["boundary"], strategy=["Check endpoints"])
    genes.save_gene(gene)
    genes.save_gene(gene)
    assert genes.get_gene(ref) == gene
    with pytest.raises(ValueError, match="different content"):
        genes.save_gene(gene.model_copy(update={"strategy": ["Changed"]}))
    with pytest.raises(ValueError, match="asset_id"):
        genes.get_gene(ref.model_copy(update={"asset_id": "wrong"}))
    provision = Provision(
        provision_id="fixed-1", run_id="run-a", requested=2,
        members=[BUILDER, REVIEWER], quota=2,
    )
    store.save_provision(provision)
    assert store.get_provision("run-a", "fixed-1") == provision
    store.close()


def test_identity_and_envelope_lineage() -> None:
    assert BUILDER != AgentId(role="builder", instance=1)
    assert len({BUILDER, AgentId(role="builder", instance=1)}) == 2
    with pytest.raises(ValidationError):
        Envelope.model_validate(event().model_dump() | {"task_id": "other"})
    with pytest.raises(ValidationError):
        Envelope.model_validate(event().model_dump() | {"provenance": "replay"})
    with pytest.raises(ValidationError):
        Envelope.model_validate(event().model_dump() | {"ts": float("nan")})


@pytest.mark.parametrize("provenance", ["mock", "replay"])
@pytest.mark.parametrize("dimension", ["interface_live", "task_live"])
def test_nonlive_cannot_claim_live(provenance: str, dimension: str) -> None:
    with pytest.raises(ValidationError, match="live acceptance"):
        Acceptance.model_validate({
            "provenance": provenance, "original_run_uri": "file:///original",
            dimension: "passed",
        })


def test_success_requires_independent_evidence() -> None:
    base = {"run_id": "run-a", "task_id": "repair", "attempt": ATTEMPT, "status": "succeeded"}
    with pytest.raises(ValidationError, match="independent"):
        TaskResult.model_validate(base)
    own_verdict = Verification(
        passed=True, reviewer=BUILDER, exit_code=0, evidence=["self-report"]
    )
    with pytest.raises(ValidationError, match="own work"):
        TaskResult.model_validate(base | {"verdict": own_verdict, "artifact_uri": "file:///x"})
    with pytest.raises(ValidationError):
        Verification(passed=True, reviewer=REVIEWER, exit_code=0)
    assert Usage().tokens is None
    assert Usage().cost_usd is None
    assert Usage(tokens=0, cost_usd=0).tokens == 0


@pytest.mark.parametrize("path", [
    "../other", "C:/outside", "/outside", "..\\other", "\\outside",
    ".", "./", "sub/file:stream", "NUL", "sub/CON.txt", "sub./file", " ",
])
def test_runtime_path_boundary(path: str) -> None:
    with pytest.raises(ValidationError):
        RunConfig(run_id="r", workspace="work", writable_paths=[path])


def test_runtime_approval_and_quota() -> None:
    with pytest.raises(ValidationError):
        RunConfig.model_validate({
            "run_id": "r", "workspace": "work", "writable_paths": ["sample.py"],
            "publication_approval_required": False,
        })
    with pytest.raises(ValidationError, match="unique"):
        Provision(provision_id="p", run_id="r", requested=2, members=[BUILDER, BUILDER])
    with pytest.raises(ValidationError, match="quota"):
        Provision(provision_id="p", run_id="r", requested=2, members=[BUILDER, REVIEWER], quota=1)


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), -float("inf")])
def test_runtime_cost_rejects_nonfinite(amount: float) -> None:
    with pytest.raises(ValidationError):
        RunConfig(run_id="r", workspace="work", writable_paths=["sample.py"], max_cost_usd=amount)
    with pytest.raises(ValidationError):
        Usage(cost_usd=amount)


def test_replay_result_and_acceptance_bind_same_original_run(tmp_path: Path) -> None:
    acceptance = Acceptance(provenance="replay", original_run_uri="file:///original-a")
    fields = {
        "run_id": "replay-run", "task_id": "repair", "attempt": ATTEMPT,
        "status": "pending_review", "provenance": "replay", "acceptance": acceptance,
        "original_run_uri": "file:///original-a",
    }
    result = TaskResult.model_validate(fields)
    with pytest.raises(ValidationError, match="original_run_uri"):
        TaskResult.model_validate(fields | {"original_run_uri": "file:///original-b"})
    store = SQLiteStore(tmp_path / "replay.db")
    store.save_result(result)
    assert store.get_result("replay-run", ATTEMPT) == result
    with pytest.raises(ValidationError, match="original_run_uri"):
        store.save_result(result.model_copy(update={"original_run_uri": "file:///original-b"}))
    store.close()
