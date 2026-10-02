"""Official stdio and GEP with protected fixed-output configuration; L1 mock only."""
import asyncio
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from contracts.identity import AgentId
from tests.experiments.generated_helpers import GENERATED_CODE
from tests.research.test_dynamic_service import setup


def test_official_stdio_generated_member_loop_and_independent_acceptance(tmp_path: Path) -> None:
    service, plan = setup(tmp_path)
    config = tmp_path / "author.json"
    config.write_text(service.config.model_dump_json(), encoding="utf-8")
    review_config = tmp_path / "reviewer.json"
    review_config.write_text(service.config.model_copy(update={"worker_id": "reviewer",
        "agent": AgentId(role="reviewer", instance=2)}).model_dump_json(), encoding="utf-8")

    async def call(session: ClientSession, name: str, args: dict) -> dict:
        result = await session.call_tool(name, args)
        assert not result.isError, result
        assert isinstance(result.structuredContent, dict)
        return result.structuredContent

    async def run() -> None:
        params = StdioServerParameters(command=sys.executable,
            args=["-m", "swarm.research", "--config", str(config)],
            env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as author:
                await author.initialize()
                assert len((await author.list_tools()).tools) == 23
                context = await call(author, "research_project", {"action": "read", "project_id": plan.project_id})
                assert context["project"]["goal"] == "approved fixture goal"
                proposal = await call(author, "propose_research_work", {
                    "project_id": plan.project_id, "kind": "experiment", "goal": "new dynamically proposed test",
                    "justification": "check the current hypothesis", "expected_contribution": "bounded fixture evidence",
                    "branch_id": plan.branch_id})
                task = proposal["task_id"]
                await call(author, "discover_tasks", {"limit": 10})
                choice = await call(author, "choose_research_work", {"task_id": task, "reason": "inspect current hypothesis"})
                assert choice["selected"] == task
                held = await call(author, "lease_task", {"action": "claim", "task_id": task, "ttl_seconds": 300})
                token = held["token"]
                prepared = await call(author, "prepare_candidate_experiment", {"task_id": task, "token": token,
                    "plan": plan.model_copy(update={"task_id": task}).model_dump(mode="json"),
                    "files": {"experiment.py": GENERATED_CODE}})
                asset = prepared["asset_id"]
                assert prepared["provenance"] == "mock" and not prepared["execution_started"]
                await call(author, "admit_candidate_experiment", {"task_id": task, "token": token})
                executed = await call(author, "research_experiment", {"action": "run", "task_id": task, "token": token})
                assert executed["result"]["provenance"] == "mock"
                assert executed["result"]["usage"] is None and executed["result"]["cost_usd"] is None
                run_id = executed["run_id"]
                artifact = await call(author, "research_experiment", {"action": "artifact", "task_id": task,
                    "run_id": run_id, "artifact_path": "outputs/output.json"})
                assert artifact["archive_status"] == "verified" and artifact["provenance"] == "mock"
                await call(author, "verify_research", {"task_id": task, "token": token, "asset_id": asset,
                    "run_id": run_id, "purpose": "original"})
                completed = await call(author, "complete_research_task", {
                    "task_id": task, "token": token, "asset_id": asset, "run_id": run_id})
                assert not (await call(author, "accept_result", {"result_id": completed["result_id"]}))["accepted"]
                duplicate = await author.call_tool("research_experiment", {"action": "run", "task_id": task, "token": token})
                assert duplicate.isError
        review_params = StdioServerParameters(command=sys.executable,
            args=["-m", "swarm.research", "--config", str(review_config)],
            env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        async with stdio_client(review_params) as (reader, writer):
            async with ClientSession(reader, writer) as reviewer:
                await reviewer.initialize()
                proposal = await call(reviewer, "propose_research_work", {"project_id": plan.project_id,
                    "kind": "experiment", "goal": "independent reproduction", "justification": "inspect original raw result",
                    "expected_contribution": "independent evidence", "branch_id": plan.branch_id, "dependencies": [task]})
                review_task = proposal["task_id"]
                held = await call(reviewer, "lease_task", {"action": "claim", "task_id": review_task, "ttl_seconds": 300})
                review_token = held["token"]
                review_plan = dict(prepared["plan"], task_id=review_task)
                await call(reviewer, "prepare_candidate_experiment", {"task_id": review_task, "token": review_token,
                    "plan": review_plan, "asset_id": asset, "purpose": "reproduction"})
                reproduced = await call(reviewer, "research_experiment", {
                    "action": "run", "task_id": review_task, "token": review_token})
                assert reproduced["result"]["provenance"] == "mock"
                assert reproduced["result"]["sandbox_id"] != executed["result"]["sandbox_id"]
                await call(reviewer, "verify_research", {"task_id": review_task, "token": review_token,
                    "asset_id": asset, "run_id": reproduced["run_id"], "purpose": "reproduction"})
                await call(reviewer, "complete_research_task", {"task_id": review_task, "token": review_token,
                    "asset_id": asset, "run_id": reproduced["run_id"]})
                accepted = await call(reviewer, "accept_result", {"result_id": completed["result_id"]})
                assert accepted["accepted"]
                follow = await call(reviewer, "propose_research_work", {"project_id": plan.project_id,
                    "kind": "question", "goal": "follow accepted result", "justification": completed["result_id"],
                    "expected_contribution": "new work", "branch_id": plan.branch_id})
                choice = await call(reviewer, "choose_research_work", {"task_id": follow["task_id"], "reason": "follow evidence"})
                assert completed["result_id"] in choice["opportunity"]["supported_by"]
                held = await call(reviewer, "lease_task", {"action": "claim", "task_id": follow["task_id"]})
                assert held["research_selection"]["result_references"] == [completed["result_id"]]
                package = await call(reviewer, "research_project", {"action": "export", "project_id": plan.project_id})
                assert len(package["executions"]) == 2
                assert package["adoption_receipts"] == []
                assert not package["completion_claim"]
                assert all(e["archive_status"] == "verified" for e in package["executions"])
        starts = [e for e in service.ledger.audit() if e["event"] == "execution_unconfirmed"]
        assert len(starts) == 2

    asyncio.run(run())
