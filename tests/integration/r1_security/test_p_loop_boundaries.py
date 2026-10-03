"""Additional coordinator-authorized product review; no eight-phase mock PASS.

Explicit product source required. Uncertain fixtures exercise refusal only;
known context is read from the actual HostConfig-bound core service/ledger.
"""
import os
import importlib.util
from types import SimpleNamespace

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE") and os.environ.get("R1_SECURITY_INSTALLED") != "1":
    pytest.skip("P source not selected; product acceptance NOT_RUN", allow_module_level=True)

legacy_loop = importlib.util.find_spec("morph_research.loop") is not None
if legacy_loop:
    from morph_research.loop import allowed_step, run_step
from morph_research.r1 import R1Envelope, ResearchGoal
from morph_research.web.r1 import R1Spaces, export_view
from tests.integration.r1_security.test_a_host_boundaries import seeded
from swarm.models import Signal


SPACE = "a" * 32
APPROVED = {"approved": True, "budget_mode": "enforceable_cap", "cash_budget_cny": 1}
legacy_only = pytest.mark.skipif(not legacy_loop,
    reason="unsafe product loop removed; native core loop integration remains NOT_RUN")


@pytest.fixture
def product_spaces(tmp_path):
    spaces = R1Spaces(SimpleNamespace(root=tmp_path / "product"))
    spaces.create(SPACE, "Q boundary", ResearchGoal(objective="read existing facts"), None)
    try:
        yield spaces
    finally:
        spaces.close()


@pytest.fixture
def product_store(product_spaces):
    return product_spaces.store(SPACE)


def assert_no_unconnected_science(package):
    # Scientific rows now come from the public core projection. The product
    # store holds inputs only; a synthetic "not_run" scientific row is not a fact.
    assert package["three_axis"] == []
    assert package["research_package"] is None
    assert package["authorization"] is None and package["route"] is None
    assert package["backend"] == {"status": "not_connected", "core_sha": None, "provenance": None}
    assert package["research"]["project"] is None
    for name in ("notes_unverified", "notes_verified", "proposals", "events", "hypotheses", "branches"):
        assert package["research"][name] == []


class UncertainBackend:
    kind = "mock"

    def __init__(self):
        self.calls = 0

    def loop_step(self, space_id, step, payload):
        self.calls += 1
        return {"provenance": "mock", "accepted": False, "effect_state": "unknown",
                "execution_state": "unknown", "result": {"reason": "Q deterministic uncertainty"}}


@legacy_only
def test_unapproved_envelope_prevents_backend_effect(product_store):
    backend = UncertainBackend()
    with pytest.raises(RuntimeError):
        run_step(SPACE, "context", {}, product_store, {"approved": False}, backend)
    assert backend.calls == 0
    assert product_store.loop_position(SPACE) is None


@legacy_only
def test_unknown_backend_result_cannot_enable_retry_or_phase_advance(product_store):
    backend = UncertainBackend()
    try:
        run_step(SPACE, "context", {}, product_store, APPROVED, backend)
    except RuntimeError:
        pass
    allowed = allowed_step(SPACE, product_store, APPROVED, backend)
    assert not allowed["enabled"], "mock label concealed unknown/refused effect and enabled another step"
    before = backend.calls
    with pytest.raises(RuntimeError):
        run_step(SPACE, "context", {}, product_store, APPROVED, backend)
    assert backend.calls == before


@legacy_only
def test_known_bound_core_context_not_blocked_just_by_provenance(tmp_path, product_store):
    core_root = tmp_path / "core"
    core_root.mkdir()
    core = seeded(core_root)
    core.ledger.enqueue(Signal(task_id="context-task", workspace=core.config.workspace, scope="science",
                               kind="opportunity", required_capability="research"))
    trusted_context = core.context("context-task")
    assert core.ledger.get("context-task").owner is None

    class BoundContextBackend:
        kind = "core"

        def loop_step(self, space_id, step, payload):
            return {"provenance": "contract_local", "effect_state": "known", "accepted": True,
                    "result": trusted_context}

    backend = BoundContextBackend()
    product_store.record_loop(SPACE, "context", "contract_local", backend.loop_step(SPACE, "context", {}))
    allowed = allowed_step(SPACE, product_store, APPROVED, backend)
    assert allowed["enabled"], "known read-only core ledger fact rejected solely for non-mock provenance"
    assert core.ledger.get("context-task").owner is None


def test_product_has_no_parallel_phase_or_execution_authority(product_store):
    assert not legacy_loop, "product loop still carries parallel execution authority"
    assert not callable(getattr(product_store, "record_loop", None))
    assert not callable(getattr(product_store, "loop_position", None))
    assert set(product_store.export_package(SPACE)).isdisjoint({"three_axis", "research", "research_package"})


@pytest.mark.parametrize("approved", [False, True])
def test_product_envelope_is_input_and_does_not_certify_science(product_store, product_spaces, approved):
    product_store.set_envelope(SPACE, R1Envelope(target="fixture", approved=approved,
        budget_mode="enforceable_cap", cash_budget_cny=1))
    package = export_view(SPACE, product_spaces)
    assert package["envelope"]["approved"] is False
    assert any(event["payload"].get("approved") is approved for event in package["events"])
    assert_no_unconnected_science(package)
    assert package["backend"]["status"] == "not_connected"


@pytest.mark.parametrize("provenance", ["mock", "replay", "contract_local"])
def test_product_event_labels_cannot_claim_or_complete_core_task(tmp_path, product_store, product_spaces, provenance):
    core_root = tmp_path / "core"
    core_root.mkdir()
    core = seeded(core_root)
    core.ledger.enqueue(Signal(task_id="core-task", workspace=core.config.workspace, scope="science",
                               kind="opportunity", required_capability="research"))
    before = core.ledger.get("core-task")
    product_store.record_event(SPACE, "execution", {"task_id": "core-task", "provenance": provenance,
        "effect_state": "unknown", "execution": "succeeded", "hypothesis": "supported",
        "contribution": "accepted", "reviewer": "invented"})
    assert core.ledger.get("core-task") == before
    package = export_view(SPACE, product_spaces)
    assert any(event["kind"] == "execution" and event["payload"]["task_id"] == "core-task"
               for event in package["events"])
    assert_no_unconnected_science(package)
