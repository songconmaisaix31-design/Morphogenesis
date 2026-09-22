"""Optional ORCA supply-plane adapter with a deterministic local fallback.

The package deliberately contains no ORCA transport implementation.  A
runtime adapter may implement :class:`OrcaProvisioner` when an official
endpoint and contract are supplied; otherwise ``ProvisioningService`` uses
``FixedProvisioner``.
"""

from orca_provision.fixed import FixedProvisioner
from orca_provision.models import IdentityBinding, ProvisionedSwarm
from orca_provision.policy import BudgetGate, ProvisioningRejected
from orca_provision.protocols import OrcaProvisioner
from orca_provision.service import ProvisioningService

__all__ = [
    "BudgetGate",
    "FixedProvisioner",
    "IdentityBinding",
    "OrcaProvisioner",
    "ProvisionedSwarm",
    "ProvisioningRejected",
    "ProvisioningService",
]
