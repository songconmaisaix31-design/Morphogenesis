"""Deterministic fixed-size fallback used when ORCA configuration is absent."""

from collections.abc import Sequence

from contracts.identity import AgentId, Role
from contracts.runtime import Provision

from orca_provision.policy import ProvisioningRejected

DEFAULT_ROLES: tuple[Role, ...] = ("planner", "builder", "reviewer", "aggregator")


class FixedProvisioner:
    """Provide a bounded, local swarm without starting any agent process."""

    def __init__(
        self,
        size: int = len(DEFAULT_ROLES),
        *,
        quota: int | None = None,
        roles: Sequence[Role] = DEFAULT_ROLES,
    ) -> None:
        if size < 1:
            raise ValueError("fixed provision size must be positive")
        role_values = tuple(roles)
        if not role_values or size > len(role_values):
            raise ValueError("fixed provision size exceeds the configured role roster")
        if quota is not None and quota < 1:
            raise ValueError("provision quota must be positive")
        self._size = size
        self._quota = quota if quota is not None else size
        self._roles = role_values

    @property
    def size(self) -> int:
        return self._size

    @property
    def quota(self) -> int:
        return self._quota

    def provision(self, run_id: str, count: int) -> Provision:
        if not run_id:
            raise ValueError("run_id must not be empty")
        if count < 1:
            raise ValueError("provision count must be positive")
        if count > self._size:
            raise ProvisioningRejected(
                f"fixed fallback supports at most {self._size} members, requested {count}"
            )
        if count > self._quota:
            raise ProvisioningRejected(
                f"provision quota {self._quota} rejects requested count {count}"
            )
        return Provision(
            provision_id=f"fixed:{run_id}:{count}",
            run_id=run_id,
            source="fixed",
            requested=count,
            members=[AgentId(role=role, instance=0) for role in self._roles[:count]],
            quota=self._quota,
            provenance="live",
            external_ids={},
        )
