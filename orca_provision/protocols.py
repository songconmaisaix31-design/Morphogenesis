"""The only boundary an eventual ORCA adapter needs to implement."""

from typing import Protocol

from contracts.runtime import Provision


class OrcaProvisioner(Protocol):
    """Opaque remote supply boundary.

    The method intentionally says nothing about HTTP, CLI, authentication,
    payloads, or lifecycle semantics.  Those details must come from a future
    published ORCA contract.  ``external_ids`` in ``Provision`` remain an
    opaque mapping at this boundary.
    """

    def provision(self, run_id: str, count: int) -> Provision: ...
