"""Selection between an explicitly supplied adapter and local fallback."""

from contracts.identity import AttemptId
from contracts.results import Usage
from contracts.runtime import Provision, StopReason

from orca_provision.fixed import FixedProvisioner
from orca_provision.models import IdentityBinding, ProvisionedSwarm
from orca_provision.policy import BudgetGate, ProvisioningRejected
from orca_provision.protocols import OrcaProvisioner


class ProvisioningService:
    """Supply metadata only; it never launches or manages agent processes."""

    def __init__(
        self,
        remote: OrcaProvisioner | None = None,
        *,
        fallback: FixedProvisioner | None = None,
        budget_gate: BudgetGate | None = None,
    ) -> None:
        self._remote = remote
        self._fallback = fallback or FixedProvisioner()
        self._budget_gate = budget_gate

    @property
    def uses_fallback(self) -> bool:
        return self._remote is None

    def provision(
        self,
        run_id: str,
        count: int,
        *,
        usage: Usage | None = None,
        stop_reason: StopReason | None = None,
    ) -> Provision:
        if count < 1:
            raise ValueError("provision count must be positive")
        if self._budget_gate is not None:
            if usage is None:
                raise ProvisioningRejected(
                    "budget usage is required when a provisioning budget gate is configured"
                )
            self._budget_gate.check(usage, stop_reason)
        elif stop_reason is not None:
            raise ProvisioningRejected(
                f"run is stopped ({stop_reason}); no additional members may be provisioned"
            )

        provision = (
            self._fallback.provision(run_id, count)
            if self._remote is None
            else self._remote.provision(run_id, count)
        )
        if provision.run_id != run_id:
            raise ProvisioningRejected("provision response run_id does not match request")
        if provision.requested != count:
            raise ProvisioningRejected("provision response requested count does not match request")
        if len(provision.members) > count:
            raise ProvisioningRejected("provision response exceeds requested count")
        return provision

    def provision_swarm(
        self,
        run_id: str,
        count: int,
        task_id: str,
        *,
        attempt: int = 0,
        usage: Usage | None = None,
        stop_reason: StopReason | None = None,
    ) -> ProvisionedSwarm:
        if not task_id:
            raise ValueError("task_id must not be empty")
        if attempt < 0:
            raise ValueError("attempt must not be negative")
        provision = self.provision(
            run_id,
            count,
            usage=usage,
            stop_reason=stop_reason,
        )
        bindings = [
            IdentityBinding(
                role=agent.role,
                agent_id=agent,
                attempt_id=AttemptId(task_id=task_id, agent=agent, attempt=attempt),
            )
            for agent in provision.members
        ]
        return ProvisionedSwarm(
            provision=provision,
            bindings=bindings,
            external_ids=dict(provision.external_ids),
        )
