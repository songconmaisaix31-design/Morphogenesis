"""Local source versions and expert applicability are append-only product facts."""
import os

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; material identity NOT_RUN", allow_module_level=True)

from morph_research.r1 import ExpertOpinion, ResearchGoal, Source
from morph_research.r1_store import R1Store

SPACE = "a" * 32


def source(**changes):
    return Source(id="b" * 32, kind="repository", identifier="local-fixture-repository",
        version="1" * 40, retrieval="parse_failed", parse_note="original first failure",
        fetched_at="2026-10-03T00:00:00Z", **changes)


@pytest.mark.parametrize("changed", ["version", "digest", "extraction"])
def test_source_change_preserves_prior_version_and_first_failure(tmp_path, changed):
    initial = source()
    updates = {"id": "c" * 32}
    if changed == "version":
        updates["version"] = "2" * 40
    elif changed == "digest":
        updates["content_sha256"] = "d" * 64
    else:
        updates.update(retrieval="present", excerpt="actual fixture extraction", parse_note=None)
    successor = initial.model_copy(update=updates)
    with R1Store(tmp_path / "product.db") as store:
        store.create_space(SPACE, "Q", ResearchGoal(objective="local material identity"))
        assert store.import_source(SPACE, initial)["created"]
        receipt = store.import_source(SPACE, successor)
        assert receipt["created"] and receipt["id"] == successor.id, "different source version silently discarded"
        sources = {row["id"]: row for row in store.sources(SPACE)}
        assert set(sources) == {initial.id, successor.id}
        assert sources[initial.id]["retrieval"] == "parse_failed"
        assert sources[initial.id]["parse_note"] == "original first failure"
    with R1Store(tmp_path / "product.db") as reopened:
        assert len(reopened.sources(SPACE)) == 2


def test_source_identical_acquisition_retry_deduplicates(tmp_path):
    initial = source()
    retry = initial.model_copy(update={"id": "c" * 32, "fetched_at": "2026-10-03T00:01:00Z"})
    with R1Store(tmp_path / "product.db") as store:
        store.create_space(SPACE, "Q", ResearchGoal(objective="local material identity"))
        store.import_source(SPACE, initial)
        assert store.import_source(SPACE, retry) == {
            "id": initial.id, "created": False, "retrieval": initial.retrieval}
        assert len(store.sources(SPACE)) == 1


@pytest.mark.parametrize("changed,value", [("applies_to", "branch-b"), ("domain", "different-domain"),
    ("at", "2026-10-03T01:00:00Z"), ("status", "dispute")])
def test_expert_opinion_applicability_does_not_disappear_in_dedup(tmp_path, changed, value):
    initial = ExpertOpinion(id="b" * 32, source="fixture-reviewer", at="2026-10-03T00:00:00Z",
        domain="fixture-domain", applies_to="branch-a", text="bounded opinion", status="opinion")
    successor = initial.model_copy(update={"id": "c" * 32, changed: value})
    with R1Store(tmp_path / "product.db") as store:
        store.create_space(SPACE, "Q", ResearchGoal(objective="scoped opinions"))
        assert store.add_opinion(SPACE, initial)["created"]
        receipt = store.add_opinion(SPACE, successor)
        assert receipt["created"] and receipt["id"] == successor.id, "distinct opinion applicability silently discarded"
        opinions = {row["id"]: row for row in store.opinions(SPACE)}
        assert set(opinions) == {initial.id, successor.id}
        assert opinions[initial.id][changed] == getattr(initial, changed)
        assert opinions[successor.id][changed] == value
        assert opinions[initial.id]["status"] == "opinion"


def test_identical_opinion_retry_returns_original(tmp_path):
    initial = ExpertOpinion(id="b" * 32, source="fixture-reviewer", applies_to="branch-a", text="bounded opinion")
    with R1Store(tmp_path / "product.db") as store:
        store.create_space(SPACE, "Q", ResearchGoal(objective="scoped opinions"))
        store.add_opinion(SPACE, initial)
        assert store.add_opinion(SPACE, initial.model_copy(update={"id": "c" * 32})) == {
            "id": initial.id, "created": False}
        assert len(store.opinions(SPACE)) == 1
