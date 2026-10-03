"""Official MCP v1 FastMCP exposes a small, identity-bound research surface."""
import asyncio
from mcp.server.fastmcp import FastMCP
from pydantic import JsonValue
from typing import Literal

from local_assets.models import Candidate
from swarm.research.policy import CorrectionKind
from swarm.research.records import NoteKind, ProposalKind, SourceRef
from swarm.research.service import Purpose, ResearchService


def create_server(service: ResearchService) -> FastMCP:
    mcp = FastMCP("Morphogenesis Research", instructions=(
        f"Host-bound research project: {service.config.project_id!r}. "
        "Read shared project context and sources, propose justified work within the approved goal, "
        "discover current legal opportunities, choose or override with a reason, then voluntarily claim one. "
        "Identity, project approval, data scope, backend, evaluation and budgets are host-bound. "
        "Renew the lease during work. Execution, scientific criteria, independent reproduction and actual adoption "
        "are separate facts. Prepare new candidate Python through the structured tools; never execute candidate "
        "code using host shell, imports or native agent tools. Mock results remain mock. "
        "Unknown external effects must not be replayed."))

    @mcp.tool()
    def discover_tasks(limit: int = 100) -> list[dict[str, JsonValue]]:
        """Discover eligible tasks in this host's scope; never auto-assign."""
        return service.discover(limit)

    @mcp.tool()
    def choose_research_work(task_id: str | None = None, reason: str = "", limit: int = 100) -> dict[str, JsonValue]:
        """Choose a current legal research opportunity; lease_task still rechecks and claims it."""
        return service.choose(task_id, reason=reason, limit=limit)

    @mcp.tool()
    async def prepare_candidate_experiment(task_id: str, token: int, plan: dict[str, JsonValue],
                                            files: dict[str, str] | None = None, asset_id: str | None = None,
                                            purpose: Purpose = "original") -> dict[str, JsonValue]:
        """Check generated Python and freeze an approved plan; candidate text is never host-executed."""
        return await asyncio.to_thread(service.prepare_candidate_experiment, task_id, token, plan, files,
                                       asset_id=asset_id, purpose=purpose)

    @mcp.tool()
    def admit_candidate_experiment(task_id: str, token: int) -> dict[str, JsonValue]:
        """Recheck frozen plan, verified isolation and project budget; execution is a separate action."""
        return service.admit_candidate_experiment(task_id, token)

    @mcp.tool()
    def project_context(task_id: str, limit: int = 100) -> dict[str, JsonValue]:
        """Read local branch/dependency/citation context; this grants no claim permission."""
        return service.context(task_id, limit=limit)

    @mcp.tool()
    def lease_task(action: Literal["claim", "renew", "release", "handoff"], task_id: str,
                   token: int | None = None, ttl_seconds: float = 60, next_worker_id: str | None = None,
                   partial: dict[str, JsonValue] | None = None) -> dict[str, JsonValue] | bool | None:
        """Actively claim/renew/release/handoff one lease as the bound identity; handoff never auto-assigns."""
        if action == "claim":
            if token is not None or next_worker_id is not None or partial is not None:
                raise ValueError("claim_accepts_only_task_and_ttl")
            return service.claim(task_id, ttl_seconds)
        if token is None:
            raise ValueError("current_fencing_token_required")
        if action == "handoff":
            if next_worker_id is None:
                raise ValueError("handoff_target_required")
            return service.handoff(task_id, token, next_worker_id, partial)
        if next_worker_id is not None or partial is not None:
            raise ValueError("handoff_arguments_require_handoff_action")
        if action == "renew":
            return service.renew(task_id, token, ttl_seconds)
        return service.release(task_id, token)

    @mcp.tool()
    def search_evidence(query: str, limit: int = 20) -> list[dict[str, JsonValue]]:
        """Search existing candidate/evidence/experience assets; retrieval is not adoption."""
        return service.search(query, limit)

    @mcp.tool()
    async def research_experiment(action: Literal["request", "run", "result", "artifact"], task_id: str,
                                  token: int | None = None, run_id: str | None = None,
                                  artifact_path: str | None = None, max_bytes: int = 65536) -> dict[str, JsonValue]:
        """Inspect a frozen plan, execute via the selected host backend, or reread its archive; never replay unknown."""
        if action == "artifact":
            if token is not None or run_id is None or artifact_path is None:
                raise ValueError("artifact_requires_bound_run_and_artifact_path")
            return service.artifact(task_id, run_id, artifact_path, max_bytes=max_bytes)
        if artifact_path is not None or max_bytes != 65536:
            raise ValueError("artifact_arguments_require_artifact_action")
        if action == "result":
            if run_id is None or token is not None:
                raise ValueError("result_requires_run_id_only")
            return service.result(task_id, run_id)
        if token is None or run_id is not None:
            raise ValueError("request_or_run_requires_current_token_only")
        if action == "request":
            return service.environment(task_id, token)
        return await service.execute(task_id, token)

    @mcp.tool()
    async def research_candidate(action: Literal["submit", "validate_files"], task_id: str, token: int,
                           candidate: Candidate | None = None, asset_id: str | None = None) -> str | dict[str, JsonValue]:
        """Submit to quarantine or run trusted static/file validation; these do not certify the science."""
        if action == "submit":
            if candidate is None or asset_id is not None:
                raise ValueError("submit_requires_candidate_only")
            return await asyncio.to_thread(service.publish, task_id, token, candidate)
        if asset_id is None or candidate is not None:
            raise ValueError("validate_files_requires_asset_id_only")
        return await asyncio.to_thread(service.validate_files, task_id, token, asset_id)

    @mcp.tool()
    def verify_research(task_id: str, token: int, asset_id: str, run_id: str,
                        purpose: Purpose) -> dict[str, JsonValue]:
        """Read raw archived evidence via the trusted evaluator; no Agent-reported metrics."""
        return service.observe(task_id, token, asset_id, run_id, purpose)

    @mcp.tool()
    def approve_candidate(task_id: str, token: int, asset_id: str, report_id: str) -> dict[str, JsonValue]:
        """Request gated local approval; requires static checks and independent clean reproduction."""
        return service.approve(task_id, token, asset_id, report_id)

    @mcp.tool()
    def complete_research_task(task_id: str, token: int, asset_id: str, run_id: str) -> dict[str, JsonValue]:
        """Submit trusted research evidence and free the scope while replication/approval is pending."""
        return service.complete_research(task_id, token, asset_id, run_id)

    @mcp.tool()
    def inherit_experience(task_id: str, token: int, asset_id: str, path_map: dict[str, str],
                           preimages: dict[str, str | None], base_revision: str,
                           base_head: str | None = None) -> dict[str, JsonValue]:
        """Inject and actually reuse asset bytes after local scientific revalidation; no adoption yet."""
        return service.inherit(task_id, token, asset_id, path_map, preimages, base_revision, base_head)

    @mcp.tool()
    def apply_candidate(task_id: str, token: int, asset_id: str, report_id: str,
                        execution_id: str | None = None) -> dict[str, JsonValue]:
        """Apply approved bytes through the existing ledger fence and record actual adoption."""
        return service.apply(task_id, token, asset_id, report_id, execution_id)

    @mcp.tool()
    def research_project(action: Literal["create", "read", "export"], project_id: str,
                         goal: str | None = None, allowed_domains: list[str] | None = None,
                         data_bounds: dict[str, str] | None = None,
                         milestones: list[str] | None = None, task_id: str | None = None,
                         branch_id: str | None = None, limit: int = 100,
                         overview: bool = False) -> dict[str, JsonValue]:
        """Read local context by default; explicit overview/export reads bounded project facts."""
        if action != "read" and (task_id is not None or branch_id is not None or overview):
            raise ValueError("context_focus_requires_read_action")
        if action == "create":
            if goal is None:
                raise ValueError("create_requires_goal")
            return service.create_project(project_id, goal, allowed_domains=tuple(allowed_domains or ()),
                                          data_bounds=data_bounds or {}, milestones=tuple(milestones or ()))
        if action == "export":
            return service.research_package(project_id, limit=limit)
        return service.research_context(project_id, task_id=task_id, branch_id=branch_id,
                                        limit=limit, overview=overview)

    @mcp.tool()
    def research_branch(project_id: str, branch_id: str, title: str, goal: str,
                        parent_branch_id: str | None = None) -> dict[str, JsonValue]:
        """Open a non-pre-registered research branch; task state stays in the existing ledger."""
        return service.create_branch(project_id, branch_id, title, goal, parent_branch_id=parent_branch_id)

    @mcp.tool()
    def submit_research_note(project_id: str, kind: NoteKind, text: str,
                             source_refs: list[dict[str, JsonValue]] | None = None,
                             branch_id: str | None = None, hypothesis_id: str | None = None,
                             task_id: str | None = None, signer: str | None = None,
                             applicability: dict[str, str] | None = None,
                             references: list[str] | None = None) -> dict[str, JsonValue]:
        """Share a sourced observation/opinion. Always unverified: a member can never promote it to fact."""
        refs = tuple(SourceRef.model_validate(r) for r in (source_refs or []))
        return service.submit_note(project_id, kind, text, source_refs=refs, branch_id=branch_id,
                                   hypothesis_id=hypothesis_id, task_id=task_id, signer=signer,
                                   applicability=applicability, references=tuple(references or ()))

    @mcp.tool()
    def propose_research_work(project_id: str, kind: ProposalKind, goal: str, justification: str,
                              expected_contribution: str, scope: str | None = None,
                              required_capability: str | None = None, dependencies: list[str] | None = None,
                              source_refs: list[dict[str, JsonValue]] | None = None,
                              branch_id: str | None = None, derived_from: str | None = None) -> dict[str, JsonValue]:
        """Propose work; the host admits it into the single ledger only within host authorization."""
        refs = tuple(SourceRef.model_validate(r) for r in (source_refs or []))
        return service.propose_work(project_id, kind, goal, justification, expected_contribution,
                                    scope=scope, required_capability=required_capability,
                                    dependencies=tuple(dependencies or ()), source_refs=refs,
                                    branch_id=branch_id, derived_from=derived_from)

    @mcp.tool()
    def accept_result(result_id: str) -> dict[str, JsonValue]:
        """Independently accept one trusted result under the host-bound reviewer (never caller-supplied)."""
        return service.accept_result(result_id)

    @mcp.tool()
    def research_advisory(project_id: str | None = None) -> dict[str, JsonValue]:
        """research-v1 advisory: accepted contributions and branch opportunities (advisory only)."""
        return service.research_advisory(project_id)

    @mcp.tool()
    def research_snapshot(project_id: str | None = None) -> dict[str, JsonValue]:
        """Three-axis/context/project snapshot; separate from legacy v0.1 routing."""
        return service.research_snapshot(project_id)

    @mcp.tool()
    def record_research_correction(branch_id: str, kind: CorrectionKind, reason: str,
                                   source_ref: str) -> dict[str, JsonValue]:
        """Append a branch lifecycle correction (sleep/downgrade/reopen); history is preserved."""
        return service.record_correction(branch_id, kind, reason, source_ref)

    @mcp.tool()
    def record_research_supersession(result_id: str, reason: str, source_ref: str,
                                     superseded_by: str | None = None) -> dict[str, JsonValue]:
        """Append a contribution supersession; the original contribution is retained."""
        return service.record_supersession(result_id, reason, source_ref, superseded_by=superseded_by)

    return mcp
