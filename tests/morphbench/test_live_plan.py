"""Budget/missing-evidence invariants, independent of provider availability."""
import importlib.util
from pathlib import Path
import sys
from decimal import Decimal


ROOT = Path(__file__).resolve().parents[2] / "tools" / "morphbench"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_cases = _load("live_cases")
_plan = _load("live_plan")


def test_frozen_request_matrix_is_within_authorized_total():
    p = _plan.plan()
    ids = [t["id"] for t in p["trials"]]
    assert len(ids) == len(set(ids))
    assert sum(t["request_cap"] for t in p["trials"]) == p["request_cap"] == 232
    assert p["request_cap"] + p["unallocated_request_slots"] <= p["absolute_request_cap"] <= 256
    assert Decimal(p["per_request_admission_cny"]) * p["absolute_request_cap"] == Decimal("24")
    assert Decimal(p["planned_token_estimate_upper_cny"]) < Decimal("24") < Decimal("30")
    assert p["actual_bill_cny"] is None


def test_systems_have_equal_full_attempt_allowances_by_seed():
    for category, cap in (("code", 6), ("dynamic", 12)):
        for seed in (0, 1, 2):
            cells = [t for t in _plan.plan()["trials"] if t["category"] == category and t["seed"] == seed]
            assert {t["system"] for t in cells} == set(_plan.SYSTEMS)
            assert {t["request_cap"] for t in cells} == {cap}


def test_no_acceptance_or_gold_in_provider_material():
    for case in _cases.DEFECTS:
        material = _cases.model_material(case.name)
        assert set(material) == {"instruction", "source"}
        assert "MORPH_CHECKPOINTS" not in str(material)
        assert "test_" not in str(material)
    assert len({c.family for c in _cases.DEFECTS}) == 3
