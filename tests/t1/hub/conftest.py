from pathlib import Path

import pytest

from bridge_node import NodeAssetBridge
from contracts.identity import AgentId, AttemptId
from contracts.provenance import Acceptance
from contracts.resolution import Gene, GeneRef
from contracts.results import TaskResult, Verification
from hub_client import CapsuleEvidence, GenePolicy, HubClient, PublicationRecord


@pytest.fixture(scope="session")
def bridge() -> NodeAssetBridge:
    return NodeAssetBridge()


@pytest.fixture(scope="session")
def gene() -> Gene:
    return Gene(
        ref=GeneRef(gene_id="gene_contract_fixture"), signals_match=["fixture_error"],
        strategy=["Inspect the failing fixture", "Repair the off-by-one boundary"],
        verification=["python -m pytest tests/test_fixture.py"],
        avoid=["Do not modify acceptance tests"], provenance="mock",
    )


@pytest.fixture(scope="session")
def policy() -> GenePolicy:
    return GenePolicy(category="repair", max_files=1, forbidden_paths=["tests/**", ".git/**"])


@pytest.fixture(scope="session")
def evidence() -> CapsuleEvidence:
    attempt = AttemptId(task_id="fixture", agent=AgentId(role="builder", instance=0), attempt=0)
    result = TaskResult(
        run_id="contract-local", task_id="fixture", attempt=attempt, status="succeeded",
        verdict=Verification(
            passed=True, reviewer=AgentId(role="reviewer", instance=0),
            evidence=["fixture://verification"], exit_code=0,
        ),
        artifact_uri="fixture://repair", provenance="mock", acceptance=Acceptance(provenance="mock"),
    )
    return CapsuleEvidence(
        capsule_id="capsule_contract_fixture", summary="Mock boundary repair for contract checks",
        confidence=0.7, files_changed=1, lines_changed=2, score=0.8, result=result,
        env_fingerprint={"runtime": "python-test-fixture"}, content={"text": "Fixture only, no live run"},
    )


@pytest.fixture(scope="session")
def record(
    tmp_path_factory: pytest.TempPathFactory, gene: Gene, policy: GenePolicy,
    evidence: CapsuleEvidence, bridge: NodeAssetBridge,
) -> PublicationRecord:
    client = HubClient(bridge=bridge)
    try:
        return client.prepare(
            gene, policy, evidence, artifact_path=tmp_path_factory.mktemp("hub-record") / "bundle.json",
        )
    finally:
        client.close()


@pytest.fixture
def publication(tmp_path: Path, record: PublicationRecord) -> Path:
    path = tmp_path / "publication.json"
    path.write_text(record.model_dump_json(), encoding="utf-8")
    return path
