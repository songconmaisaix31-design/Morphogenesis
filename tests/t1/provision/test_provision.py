import pytest

from contracts.results import Usage
from contracts.runtime import RunConfig
from orca_provision import (
    BudgetGate,
    FixedProvisioner,
    ProvisioningRejected,
    ProvisioningService,
)


def test_fixed_fallback_materializes_stable_three_layer_identity() -> None:
    service = ProvisioningService()

    first = service.provision_swarm("run-1", 4, "task-1")
    second = service.provision_swarm("run-1", 4, "task-1")

    assert service.uses_fallback is True
    assert first.provision.source == "fixed"
    assert first.provision.provenance == "live"
    assert first.provision.external_ids == {}
    assert [binding.role for binding in first.bindings] == [
        "planner",
        "builder",
        "reviewer",
        "aggregator",
    ]
    assert [binding.agent_id for binding in first.bindings] == [
        binding.agent_id for binding in second.bindings
    ]
    assert all(
        binding.attempt_id.agent == binding.agent_id
        and binding.attempt_id.task_id == "task-1"
        and binding.attempt_id.attempt == 0
        for binding in first.bindings
    )


def test_quota_rejects_before_overprovisioning() -> None:
    service = ProvisioningService(fallback=FixedProvisioner(size=4, quota=2))

    with pytest.raises(ProvisioningRejected, match="quota"):
        service.provision("run-1", 3)


def test_missing_orca_configuration_degrades_to_fixed_local_supply() -> None:
    provision = ProvisioningService().provision("run-1", 2)

    assert provision.source == "fixed"
    assert provision.run_id == "run-1"
    assert len(provision.members) == 2
    assert provision.external_ids == {}


def test_negative_and_zero_requests_are_rejected() -> None:
    service = ProvisioningService()

    for count in (0, -1):
        with pytest.raises(ValueError, match="positive"):
            service.provision("run-1", count)
    with pytest.raises(ValueError, match="positive"):
        FixedProvisioner(size=0)
    with pytest.raises(ValueError, match="negative"):
        service.provision_swarm("run-1", 1, "task-1", attempt=-1)


def test_budget_exhaustion_and_stop_state_reject_supply() -> None:
    config = RunConfig(run_id="run-1", workspace="workspace", writable_paths=["."])
    service = ProvisioningService(budget_gate=BudgetGate(config))

    with pytest.raises(ProvisioningRejected, match="token budget"):
        service.provision(
            "run-1", 1, usage=Usage(tokens=config.max_tokens, cost_usd=0.1)
        )
    with pytest.raises(ProvisioningRejected, match="stopped"):
        service.provision(
            "run-1",
            1,
            usage=Usage(tokens=0, cost_usd=0),
            stop_reason="manual",
        )
    with pytest.raises(ProvisioningRejected, match="unknown"):
        service.provision("run-1", 1, usage=Usage())
