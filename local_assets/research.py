"""Scientific eligibility supplements, and never replaces, static file checks."""
import json
from local_assets.models import AssetSafetyError
from local_assets.research_models import ResearchObservation
from local_assets.store import LocalAssetStore


def matching_reports(store: LocalAssetStore, asset_id: str) -> list[ResearchObservation]:
    candidate = store.fetch(asset_id)
    claim = candidate.research
    if claim is None:
        raise AssetSafetyError("research_claim_required")
    return [r for r in store.research_reports(asset_id)
            if r.plan_id == claim.plan_id and r.criterion_version == claim.criterion_version
            and r.conditions == claim.conditions and r.candidate_json == candidate.model_dump_json()]


def scientific_plan(plan_json: str) -> str:
    """Role/local archive paths are lineage, not a scientific condition."""
    plan = json.loads(plan_json)
    if plan.get("schema_version") == "generated-experiment/v1":
        from local_assets.generated_validation import generated_conditions
        from orchestration.experiments.generated import GeneratedExperimentPlan
        return json.dumps(generated_conditions(GeneratedExperimentPlan.model_validate(plan)), sort_keys=True)
    plan.pop("role", None)
    for name in ("code", "data"):
        if isinstance(plan.get(name), dict):
            plan[name].pop("local_path", None)
    return json.dumps(plan, sort_keys=True, separators=(",", ":"))


def known_effect(report: ResearchObservation) -> bool:
    return json.loads(report.result_json).get("effect_state") in ("known", "confirmed")


def inheritance_matches(reports: list[ResearchObservation], task_id: str, worker_id: str, token: int) -> bool:
    originals = [r for r in reports if r.purpose == "original" and r.scientific_verdict == "passed"
                 and r.execution_state == "succeeded" and r.provenance == "live" and known_effect(r)]
    return any(r.purpose == "inheritance" and r.task_id == task_id and r.worker_id == worker_id
               and r.fencing_token == token and r.scientific_verdict == "passed"
               and r.execution_state == "succeeded" and r.provenance == "live" and known_effect(r)
               and any(scientific_plan(r.plan_json) == scientific_plan(a.plan_json) for a in originals)
               for r in reports)


def require_reproduced(store: LocalAssetStore, asset_id: str, *, _ancestors: tuple[str, ...] = ()) -> None:
    if asset_id in _ancestors or len(_ancestors) >= 32:
        raise AssetSafetyError("research_inheritance_cycle_or_depth")
    reports = matching_reports(store, asset_id)
    if any(r.purpose in {"original", "reproduction", "inheritance"} and r.scientific_verdict == "passed"
           and r.execution_state == "succeeded" and not known_effect(r) for r in reports):
        raise AssetSafetyError("research_report_effect_unknown")
    if any(r.purpose == "counterexample" and r.scientific_verdict == "failed" for r in reports):
        raise AssetSafetyError("research_invalidated_by_counterexample")
    if any(r.purpose == "reproduction" and r.scientific_verdict == "failed" for r in reports):
        raise AssetSafetyError("research_disputed_reproduction")
    candidate = store.fetch(asset_id)
    inherited = store.source_consumption(asset_id)
    if inherited is not None:
        if inherited.candidate != candidate or inherited.asset_id == asset_id:
            raise AssetSafetyError("research_consumption_mismatch")
        parent = store.fetch_approved(inherited.asset_id)
        if parent.research != candidate.research or candidate.research is None:
            raise AssetSafetyError("research_condition_mismatch")
        require_reproduced(store, inherited.asset_id, _ancestors=(*_ancestors, asset_id))
        context = inherited.context
        if not inheritance_matches(matching_reports(store, inherited.asset_id), context.task_id,
                                   context.worker_id, context.fencing_token):
            raise AssetSafetyError("local_revalidation_required")
        return
    originals = [r for r in reports if r.purpose == "original" and r.scientific_verdict == "passed"
                 and r.execution_state == "succeeded" and r.provenance == "live" and r.sandbox_id
                 and r.task_id == candidate.attempt.task_id and known_effect(r)]
    reproductions = [r for r in reports if r.purpose == "reproduction" and r.scientific_verdict == "passed"
                    and r.execution_state == "succeeded" and r.provenance == "live" and r.sandbox_id and known_effect(r)]
    if not any(a.worker_id != b.worker_id and a.sandbox_id != b.sandbox_id and a.run_id != b.run_id
               and scientific_plan(a.plan_json) == scientific_plan(b.plan_json) for a in originals for b in reproductions):
        raise AssetSafetyError("independent_clean_reproduction_required")


def require_inheritance(store: LocalAssetStore, asset_id: str, task_id: str,
                        worker_id: str, token: int, conditions: dict[str, str]) -> None:
    claim = store.fetch(asset_id).research
    if claim is None or claim.conditions != conditions:
        raise AssetSafetyError("research_condition_mismatch")
    require_reproduced(store, asset_id)
    if not inheritance_matches(matching_reports(store, asset_id), task_id, worker_id, token):
        raise AssetSafetyError("local_revalidation_required")
