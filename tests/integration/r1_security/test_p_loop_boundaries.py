"""Additional coordinator-authorized product review; no eight-phase mock PASS.

Explicit product source required. Uncertain fixtures exercise refusal only;
known context is read from the actual HostConfig-bound core service/ledger.
"""
import os

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE"):
    pytest.skip("P source not selected; product acceptance NOT_RUN", allow_module_level=True)

from morph_research.loop import allowed_step, run_step
from morph_research.r1 import ResearchGoal
from morph_research.r1_store import R1Store
from tests.integration.r1_security.test_a_host_boundaries import seeded
from swarm.models import Signal


SPACE = "a" * 32
APPROVED = {"approved": True, "budget_mode": "enforceable_cap", "cash_budget_cny": 1}


@pytest.fixture
def product_store(tmp_path):
    with R1Store(tmp_path / "product.db") as s:
        s.create_space(SPACE, "Q boundary", ResearchGoal(objective="read existing facts"))
        yield s


class UncertainBackend:
    kind = "mock"

    def __init__(self):
        self.calls = 0

    def loop_step(self, space_id, step, payload):
        self.calls += 1
        return {"provenance": "mock", "accepted": False, "effect_state": "unknown",
                "execution_state": "unknown", "result": {"reason": "Q deterministic uncertainty"}}


def test_unapproved_envelope_prevents_backend_effect(product_store):
    backend = UncertainBackend()
    with pytest.raises(RuntimeError):
        run_step(SPACE, "context", {}, product_store, {"approved": False}, backend)
    assert backend.calls == 0
    assert product_store.loop_position(SPACE) is None


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
