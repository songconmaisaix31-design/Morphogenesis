"""Observatory readiness: declaration-driven environment health.

The observatory must describe *any* machine it lands on, so the provider set is
data (``OBSERVATORY_PROVIDERS``) and an undeclared dimension reports
``not_run``.  Nothing here establishes run evidence.
"""
from swarm.observatory.contracts import (
    READINESS_SCHEMA,
    SUBJECTS,
    EnvironmentReport,
    ProbeResult,
    Provider,
    ProviderKind,
    ProviderState,
    ProviderSubject,
)
from swarm.observatory.manifest import (
    ENV_MANIFEST,
    EXAMPLE_MANIFEST,
    MANIFEST_SCHEMA,
    ProviderConfigError,
    build_providers,
    example_manifest_json,
    load_manifest,
)
from swarm.observatory.providers import (
    CliProvider,
    CredentialFileProvider,
    CredentialProvider,
    HostProvider,
    McpProvider,
)
from swarm.observatory.registry import BOUNDARIES, ProviderRegistry, build_registry

__all__ = [
    "BOUNDARIES",
    "ENV_MANIFEST",
    "EXAMPLE_MANIFEST",
    "MANIFEST_SCHEMA",
    "READINESS_SCHEMA",
    "SUBJECTS",
    "CliProvider",
    "CredentialFileProvider",
    "CredentialProvider",
    "EnvironmentReport",
    "HostProvider",
    "McpProvider",
    "ProbeResult",
    "Provider",
    "ProviderConfigError",
    "ProviderKind",
    "ProviderRegistry",
    "ProviderState",
    "ProviderSubject",
    "build_providers",
    "build_registry",
    "example_manifest_json",
    "load_manifest",
]
