from contracts.identity import AgentId, AttemptId
from local_assets.models import Candidate, FileChange
from local_assets.research_models import ResearchClaim


def test_nonresearch_json_keeps_legacy_nullable_fields_and_research_binds_when_present():
    candidate = Candidate(attempt=AttemptId(task_id="legacy", agent=AgentId(role="builder", instance=0), attempt=1),
                          base_revision="0" * 40, changes=(FileChange(path="example.py", before=None, after="answer = 0\n"),),
                          declared_files=1, declared_lines=1)
    body = candidate.model_dump_json()
    assert '"research"' not in body
    assert '"base_head":null' in body and '"before":null' in body and '"attempt":1' in body
    assert Candidate.model_validate_json(body).model_dump_json() == body
    researched = candidate.model_copy(update={"research": ResearchClaim(plan_id="case", criterion_version="v1",
                                        conditions={"seed": "0"}, sources=("https://example.invalid/source",))})
    assert '"research":{' in researched.model_dump_json()
    assert Candidate.model_validate_json(researched.model_dump_json()).research == researched.research
