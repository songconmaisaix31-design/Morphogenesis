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


def archived_research_chain(root, corruption=None):
    """Persist the original host result shapes; fixture facts remain mock evidence."""
    from contracts.identity import AttemptId
    from local_assets.models import (AdoptionReceipt, Candidate, ConsumptionContext, ConsumptionExecution,
                                    EnvironmentFingerprint, FileChange, PromotionReceipt, ValidationReport)
    from local_assets.research_models import ResearchClaim, ResearchObservation
    service = service_at(root)
    claim = ResearchClaim(plan_id="archived-plan", criterion_version="archived-v1",
                          conditions={"seed": "0"}, sources=("https://example.invalid/fixture",))
    candidates, assets = {}, {}
    for index, role in enumerate(("author", "replication", "inheritance")):
        plan = {"plan_id": claim.plan_id, "criteria": {"version": claim.criterion_version},
                "role": role, "seed": 0, "code": {"local_path": "archive/" + role, "sha256": "fixed"}}
        path = "science/reused.txt" if role == "inheritance" else "science/source.txt"
        policy = {"version": role + "-files-v1", "executor": "literal-files-v1",
                  "expectations": [{"path": path, "content": "fixture"}]}
        service.ledger.enqueue(Signal(task_id=role, workspace=service.config.workspace, scope="science",
                                      kind="opportunity", required_capability="research." + role),
                               dependencies=() if role == "author" else ("author",),
                               acceptance={"research_claim": claim.model_dump(mode="json"),
                                           "experiment_plan": plan, "file_policy": policy})
        lease = service.ledger.claim(role, role, locality=service.locality)
        assert lease is not None
        source_attempt = AttemptId(task_id=role, agent=AgentId(role="reviewer" if role == "replication" else "builder",
                                                            instance=index), attempt=1)
        if role == "replication":
            candidate, asset = candidates["author"], assets["author"]
        else:
            candidate = Candidate(attempt=source_attempt, base_revision="a" * 40, scope="science",
                                  changes=(FileChange(path=path, before=None, after="fixture"),),
                                  declared_files=1, declared_lines=1, research=claim)
            asset = service.store.publish(candidate)
        candidates[role], assets[role] = candidate, asset
        evaluated = {"execution_state": "succeeded", "scientific_verdict": "passed",
                     "effect_state": "known", "provenance": "mock"}
        run_id = role + "-run"
        service.ledger.begin_execution(lease, run_id, max_executions=1)
        service.ledger.record_event("research_execution", {"run_id": run_id, "worker_id": role,
                                    "token": lease.token, "result": evaluated}, task_id=role)
        service.ledger.confirm_execution(lease, run_id)
        observation = ResearchObservation(report_id=role + "-science", asset_id=assets["author"],
            task_id=role, worker_id=role, fencing_token=lease.token, run_id=run_id, sandbox_id=None,
            plan_id=claim.plan_id, criterion_version=claim.criterion_version, conditions=claim.conditions,
            plan_json=json.dumps(plan), result_json=json.dumps(evaluated),
            candidate_json=candidates["author"].model_dump_json(), provenance="mock",
            purpose={"author": "original", "replication": "reproduction", "inheritance": "inheritance"}[role],
            execution_state="succeeded", scientific_verdict="passed", created_at=service.ledger.now(),
            source_swarm_id=service.config.swarm_id, source_fencing_token=lease.token, source_attempt=source_attempt)
        if role == "replication":
            updates = {"worker": {"worker_id": "wrong"}, "token": {"fencing_token": 2},
                       "task": {"task_id": "wrong"}, "source_attempt": {"source_attempt": candidates["author"].attempt},
                       "purpose": {"purpose": "original"},
                       "unknown": {"result_json": json.dumps({**evaluated, "effect_state": "unknown"})},
                       "passed": {"result_json": json.dumps({**evaluated, "scientific_verdict": "failed"})},
                       "plan": {"plan_json": json.dumps({**plan, "seed": 1})},
                       "claim": {"conditions": {"seed": "1"}},
                       "scope": {"candidate_json": candidate.model_copy(update={"scope": "other"}).model_dump_json()}}
            observation = observation.model_copy(update=updates.get(corruption, {}))
        with service.store.connection() as db:
            db.execute("INSERT INTO research_reports VALUES (?,?,?)",
                       (observation.report_id, observation.asset_id, observation.model_dump_json()))
        if role == "author":
            service.ledger.submit(lease, role + "-result", {"asset_id": asset, "run_id": run_id,
                "stage": "evidence_submitted", "scientific_verdict": "passed", "execution_state": "succeeded", "provenance": "mock"})
            continue
        validation = ValidationReport(report_id=role + "-static", asset_id=asset, attempt=candidate.attempt,
            base_revision=candidate.base_revision, candidate_json=candidate.model_dump_json(), passed=True,
            reasons=(), actual_files=1, actual_lines=1,
            env_fingerprint=EnvironmentFingerprint(node_version="fixture", arch="fixture", platform="fixture", python_version="fixture"),
            created_at=service.ledger.now(), expires_at=service.ledger.now() + 60,
            policy_version=policy["version"], policy_json=json.dumps(policy), isolation="non_arbitrary_literal_files")
        promotion = PromotionReceipt(asset_id=asset, report_id=validation.report_id,
                                     promoted_at=validation.created_at, policy_version=validation.policy_version)
        with service.store.connection() as db:
            db.execute("INSERT INTO reports VALUES (?,?,?)", (validation.report_id, asset, validation.model_dump_json()))
            if corruption != "approval" or role != "replication":
                db.execute("INSERT INTO approvals VALUES (?,?,?)", (asset, validation.report_id, promotion.model_dump_json()))
        result = {"applied": True, "candidate_asset_id": asset}  # Archived host omitted report_id.
        if role == "replication" and corruption == "explicit_report":
            result["report_id"] = "wrong"  # Explicit wrong identity must never fall back.
        if role == "inheritance":
            context = ConsumptionContext(swarm_id=service.config.swarm_id, task_id=role, worker_id=role,
                fencing_token=lease.token, execution_id="actual-consumption", scope="science", input_context="fixture input")
            execution = ConsumptionExecution(asset_id=assets["author"], context=context, candidate=candidate,
                                             candidate_asset_id=asset, created_at=service.ledger.now())
            receipt = AdoptionReceipt(asset_id=assets["author"], candidate_asset_id=asset, context=context,
                                      result_id=role + "-result", adopted_at=service.ledger.now())
            if corruption == "adoption_context":
                receipt = receipt.model_copy(update={"context": context.model_copy(update={"worker_id": "wrong"})})
            elif corruption == "adoption_source":
                receipt = receipt.model_copy(update={"asset_id": asset})
            elif corruption == "consumption_child":
                execution = execution.model_copy(update={"candidate": candidates["author"]})
            with service.store.connection() as db:
                db.execute("INSERT INTO consumptions VALUES (?,?)", (context.execution_id, execution.model_dump_json()))
                db.execute("INSERT INTO adoptions VALUES (?,?)", (context.execution_id, receipt.model_dump_json()))
            result.update({"consumed_asset_ids": [assets["author"]], "execution_id": context.execution_id,
                           "input_context": context.input_context})
        # A fixture callback records only the ledger's applied shape; no model,
        # experiment or actual scientific adoption is claimed by these rows.
        service.ledger.submit(lease, role + "-result", result, apply=lambda owned: owned())
    return service


@pytest.mark.parametrize("corruption", [None, "worker", "token", "task", "source_attempt", "purpose", "unknown",
    "passed", "plan", "claim", "scope", "approval", "explicit_report", "adoption_context", "adoption_source", "consumption_child"])
def test_archived_replication_and_adoption_use_existing_immutable_chains(tmp_path, corruption):
    service = archived_research_chain(tmp_path, corruption)
    facts = trusted_facts(service.ledger, service.store.root)
    expected = {"author-result", "replication-result", "inheritance-result"}
    if corruption in {"adoption_context", "adoption_source", "consumption_child"}:
        expected.remove("inheritance-result")
    elif corruption is not None:
        expected.remove("replication-result")
    assert {fact.source_id for fact in facts} == expected
    assert all(fact.provenance == "mock" for fact in facts)
    if corruption is None:
        assert [(f.task_id, f.kind) for f in facts] == [("author", "scientific_result"),
            ("replication", "scientific_result"), ("inheritance", "scientific_adoption")]
        snapshot = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file()}
        assert policy_diagnostics(service.config)["feedback"] == policy_diagnostics(service.config)["feedback"]
        assert snapshot == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file()}
        service.field.synchronize(facts + facts)
        service.field.synchronize(trusted_facts(service.ledger, service.store.root))
        assert all(service.field.pipe_history(role, "research." + role, prior=0.25).samples == 1
                   for role in ("author", "replication", "inheritance"))


def test_nonempty_rollback_journal_is_refused_without_touching_archive(tmp_path):
    service = service_at(tmp_path)
    journal = Path(str(service.ledger.path) + "-journal")
    journal.write_bytes(b"uncommitted fixture archive")
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="checkpointed_archive"):
        policy_diagnostics(service.config)
    assert before == {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file()}
