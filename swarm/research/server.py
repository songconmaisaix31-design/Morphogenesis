"""Official MCP v1 FastMCP exposes a small, identity-bound research surface."""
from mcp.server.fastmcp import FastMCP
from pydantic import JsonValue

from local_assets.models import Candidate
from swarm.research.service import Purpose, ResearchService


def create_server(service: ResearchService) -> FastMCP:
    mcp = FastMCP("Morphogenesis Research", instructions=(
        "Discover eligible research tasks and voluntarily claim one. Identity and permissions are host-bound. "
        "Renew the lease during work. Execution, scientific criteria, independent reproduction and actual adoption "
        "are separate facts. Unknown external effects must not be replayed."))

    @mcp.tool()
    def discover_tasks(limit: int = 100) -> list[dict[str, JsonValue]]:
        """Discover eligible tasks in this host's scope; never auto-assign."""
        return service.discover(limit)

    @mcp.tool()
    def project_context(task_id: str) -> dict[str, JsonValue]:
        """Read task acceptance, paper/evidence references and project context."""
        return service.context(task_id)

    @mcp.tool()
    def claim_task(task_id: str, ttl_seconds: float = 60) -> dict[str, JsonValue] | None:
        """Voluntarily claim an eligible task as the bound host identity."""
        return service.claim(task_id, ttl_seconds)

    @mcp.tool()
    def renew_task(task_id: str, token: int, ttl_seconds: float = 60) -> dict[str, JsonValue]:
        """Renew a current task lease; stale tokens and other holders are rejected."""
        return service.renew(task_id, token, ttl_seconds)

    @mcp.tool()
    def release_task(task_id: str, token: int) -> bool:
        """Release a held task; an unconfirmed external request stays blocked."""
        return service.release(task_id, token)

    @mcp.tool()
    def handoff_task(task_id: str, token: int, next_worker_id: str,
                     partial: dict[str, JsonValue] | None = None) -> dict[str, JsonValue]:
        """Preserve partial work and yield; the next worker must actively claim."""
        return service.handoff(task_id, token, next_worker_id, partial)

    @mcp.tool()
    def search_evidence(query: str, limit: int = 20) -> list[dict[str, JsonValue]]:
        """Search existing candidate/evidence/experience assets; retrieval is not adoption."""
        return service.search(query, limit)

    @mcp.tool()
    def request_environment(task_id: str, token: int) -> dict[str, JsonValue]:
        """Inspect a pre-registered experiment environment request without executing."""
        return service.environment(task_id, token)

    @mcp.tool()
    async def execute_experiment(task_id: str, token: int) -> dict[str, JsonValue]:
        """Execute the trusted pre-registered plan once in a fresh sandbox."""
        return await service.execute(task_id, token)

    @mcp.tool()
    def experiment_result(task_id: str, run_id: str) -> dict[str, JsonValue]:
        """Read durable evidence for a run belonging to this scoped task."""
        return service.result(task_id, run_id)

    @mcp.tool()
    def submit_candidate(task_id: str, token: int, candidate: Candidate) -> str:
        """Publish a statically safe candidate to quarantine; acceptance cannot be changed."""
        return service.publish(task_id, token, candidate)

    @mcp.tool()
    def validate_candidate_files(task_id: str, token: int, asset_id: str) -> dict[str, JsonValue]:
        """Run the existing trusted static/file validator, separately from science."""
        return service.validate_files(task_id, token, asset_id)

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

    return mcp
