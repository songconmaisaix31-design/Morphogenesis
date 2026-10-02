import asyncio
import json
import sqlite3
import random
from pathlib import Path

import pytest

from contracts.identity import AgentId
from swarm.models import Signal
from swarm.research.models import HostConfig
from swarm.research.service import ResearchService
from swarm.feedback import policy_diagnostics
from swarm.feedback import trusted_facts


def service_at(root, first_capability="research"):
    config = HostConfig(ledger_path=str(root / "ledger.sqlite3"), swarm_id="policy-entry",
                        workspace=str(root / "project"), worker_id="worker",
                        agent=AgentId(role="builder", instance=0), authorized_scopes=("science",),
                        capabilities=(first_capability, "other"), assets_root=str(root / "assets"),
                        evidence_root=str(root / "evidence"))
    service = ResearchService(config)
    for name, capability in (("one", first_capability), ("two", "other")):
        service.ledger.enqueue(Signal(task_id=name, workspace=config.workspace, scope="science/" + name,
                                      required_capability=capability, kind="opportunity",
                                      payload={"private_provider_details": "MUST_NOT_DUMP"}))
    return service


def test_original_mcp_discovery_and_voluntary_override_are_authoritative(tmp_path):
    from swarm.research.server import create_server
    service = service_at(tmp_path)
    server = create_server(service)

    async def interact():
        _, discovered = await server.call_tool("discover_tasks", {})
        tasks = discovered["result"]
        recommendation = tasks[0]["policy_recommendation"]
        assert recommendation["policy_version"] == "v0.1"
        assert len(recommendation["probabilities"]) == 2
        assert "signals" not in tasks[1]["policy_recommendation"]
        assert tasks[1]["policy_recommendation"]["routing_sequence"] == recommendation["routing_sequence"]
        assert all(service.ledger.get(name).owner is None for name in ("one", "two"))
        actual = "two" if recommendation["selected"] == "one" else "one"
        _, claimed = await server.call_tool("lease_task", {"action": "claim", "task_id": actual})
        selection = claimed["result"]["policy_selection"]
        assert selection["overridden"] is True
        assert selection["actual_task_id"] == actual
        assert selection["routing_sequence"] == recommendation["routing_sequence"]
        assert service.ledger.get(actual).owner == "worker"
        event = next(e for e in service.ledger.audit() if e["event"] == "policy_selection")
        assert event["body"] == selection
        assert len(await server.list_tools()) == 11
    asyncio.run(interact())


def test_no_recommendation_does_not_claim_compliance_and_readonly_is_secretfree(tmp_path):
    service = service_at(tmp_path)
    response = service.claim("one")
    assert response["policy_selection"]["recommendation_present"] is False
    assert response["policy_selection"]["overridden"] is None
    service.release("one", response["token"])
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    diagnostic = policy_diagnostics(service.config)
    assert diagnostic["policy"]["routing_sequence"] is None
    assert diagnostic["policy"]["audited"] is False
    assert diagnostic["execution_invoked"] is False
    assert "MUST_NOT_DUMP" not in json.dumps(diagnostic)
    assert before == {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="new_separate"):
        policy_diagnostics(service.config, rebuild_to=Path(service.config.workspace) / "derived.sqlite3")
    assert not Path(service.config.workspace).exists()
    separate = tmp_path.parent / (tmp_path.name + "-separate.sqlite3")
    rebuilt = policy_diagnostics(service.config, rebuild_to=separate)
    assert rebuilt["rebuild"] is True and separate.is_file()
    assert all(path.read_bytes() == body for path, body in before.items())


@pytest.mark.parametrize("corruption", [None, "unknown_effect", "worker", "scope", "token", "run", "evaluated_verdict", "execution_verdict"])
def test_offline_persisted_scientific_lineage_is_required_not_caller_passed(tmp_path, corruption):
    from contracts.identity import AttemptId
    from local_assets.models import Candidate, FileChange
    from local_assets.research_models import ResearchClaim, ResearchObservation
    service = service_at(tmp_path, "research.author")
    claim = ResearchClaim(plan_id="offline-plan", criterion_version="existing-v1",
                          conditions={"input": "fixture"}, sources=("https://example.invalid/evidence",))
    plan = {"plan_id": claim.plan_id, "criteria": {"version": claim.criterion_version}}
    signal = Signal(task_id="source", workspace=service.config.workspace, scope="science/source",
                    kind="opportunity", required_capability="research.author")
    service.ledger.enqueue(signal, acceptance={"research_claim": claim.model_dump(mode="json"), "experiment_plan": plan})
    candidate = Candidate(attempt=AttemptId(task_id="source", agent=service.config.agent, attempt=1),
                          base_revision="a" * 40, scope=signal.scope,
                          changes=(FileChange(path="science/source/result.txt", before=None, after="offline fixture"),),
                          declared_files=1, declared_lines=1, research=claim)
    asset = service.store.publish(candidate)
    lease = service.ledger.claim("source", "worker", locality=service.locality)
    run_id = "offline-existing-run"
    # Static contract-local persisted evidence, no backend/experiment invocation.
    result = {"execution_state": "succeeded", "scientific_verdict": "passed", "effect_state": "known", "provenance": "mock"}
    service.ledger.begin_execution(lease, run_id, max_executions=1)
    execution_result = {**result, "scientific_verdict": "failed"} if corruption == "execution_verdict" else result
    service.ledger.record_event("research_execution", {"run_id": run_id, "worker_id": "worker", "token": 1, "result": execution_result}, task_id="source")
    service.ledger.confirm_execution(lease, run_id)
    observation = ResearchObservation(report_id="offline-report", asset_id=asset, task_id="source", worker_id="worker",
                                      fencing_token=1, run_id=run_id, sandbox_id=None, plan_id=claim.plan_id,
                                      criterion_version=claim.criterion_version, conditions=claim.conditions,
                                      plan_json=json.dumps(plan), candidate_json=candidate.model_dump_json(), result_json=json.dumps(result),
                                      provenance="mock", purpose="original", execution_state="succeeded", scientific_verdict="passed",
                                      created_at=service.ledger.now(), source_swarm_id=service.config.swarm_id,
                                      source_fencing_token=1, source_attempt=candidate.attempt)
    if corruption == "unknown_effect":
        observation = observation.model_copy(update={"result_json": json.dumps({**result, "effect_state": "unknown"})})
    elif corruption == "evaluated_verdict":
        observation = observation.model_copy(update={"result_json": json.dumps({**result, "scientific_verdict": "failed"})})
    elif corruption == "worker":
        observation = observation.model_copy(update={"worker_id": "wrong"})
    elif corruption == "scope":
        observation = observation.model_copy(update={"candidate_json": candidate.model_copy(update={"scope": "private"}).model_dump_json()})
    elif corruption == "token":
        observation = observation.model_copy(update={"fencing_token": 2})
    elif corruption == "run":
        observation = observation.model_copy(update={"run_id": "wrong"})
    # The test-only corrupt row bypasses the store's validation so the reader's
    # fail-closed behavior is checked against real immutable SQLite tables.
    with service.store.connection() as db:
        db.execute("INSERT INTO research_reports VALUES (?,?,?)", (observation.report_id, asset, observation.model_dump_json()))
    service.ledger.submit(lease, "original-result", {"asset_id": asset, "run_id": run_id, "stage": "evidence_submitted",
                                                   "scientific_verdict": "passed", "execution_state": "succeeded", "provenance": "mock"})
    facts = trusted_facts(service.ledger, service.store.root)
    assert len(facts) == (1 if corruption is None else 0)
    if facts:
        assert facts[0].provenance == "mock"
        service.field.synchronize(facts + facts)
        assert service.field.pipe_history("worker", "research.author", prior=0.25).samples == 1
        from swarm.pheromone import PreviewField
        from swarm.router import Router
        service.ledger.enqueue(Signal(task_id="third", workspace=service.config.workspace, scope="science/third",
                                      kind="opportunity", required_capability="research.author", concentration=2.0))
        # Both choices preserve the exact author capability; different original
        # observation coordinates need no new task scheduler or score formula.
        before = Router(PreviewField(service.ledger, []), strategy_version="v0.1", rng=random.Random(0)).recommend(
            "worker", service.locality, {"research.author": 1.0}, record_audit=False)
        after = policy_diagnostics(service.config.model_copy(update={"capabilities": ("research.author",)}))["policy"]
        assert len(before["probabilities"]) == len(after["probabilities"]) == 2
        assert after["probabilities"][0] < before["probabilities"][0] - 0.0001


def test_uncheckpointed_wal_is_refused_without_source_writes_or_missing_fact_claim(tmp_path):
    service = service_at(tmp_path)
    with sqlite3.connect(service.ledger.path) as writer:
        writer.execute("INSERT INTO task_audit(swarm_id,event,at,body) VALUES (?,?,?,?)",
                       (service.config.swarm_id, "test_wal_fact", 100, "{}"))
        writer.commit()
        before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
        with pytest.raises(ValueError, match="checkpointed_archive"):
            policy_diagnostics(service.config)
        assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    writer.close()
    assert policy_diagnostics(service.config)["execution_invoked"] is False
