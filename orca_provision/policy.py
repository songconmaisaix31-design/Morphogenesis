"""Local quantity and runtime-budget guards for supply requests."""

from contracts.results import Usage
from contracts.runtime import RunConfig, StopReason


class ProvisioningRejected(ValueError):
    """A supply request cannot be admitted under the supplied limits."""


class BudgetGate:
    """Reject supply after a stop condition or measured budget is exhausted.

    Usage is required when a gate is used.  ``None`` means unknown in the T0
    contract and is therefore fail-closed under ``unknown_usage_policy=stop``;
    this guard never turns unknown usage into an invented zero.
    """

    def __init__(self, config: RunConfig) -> None:
        self._config = config

    @property
    def config(self) -> RunConfig:
        return self._config

    def check(self, usage: Usage, stop_reason: StopReason | None = None) -> None:
        if stop_reason is not None:
            raise ProvisioningRejected(
                f"run is stopped ({stop_reason}); no additional members may be provisioned"
            )
        if usage.tokens is None or usage.cost_usd is None:
            raise ProvisioningRejected(
                "token/cost usage is unknown; provisioning stops under unknown_usage_policy=stop"
            )
        if usage.tokens >= self._config.max_tokens:
            raise ProvisioningRejected("token budget exhausted")
        if usage.cost_usd >= self._config.max_cost_usd:
            raise ProvisioningRejected("cost budget exhausted")
