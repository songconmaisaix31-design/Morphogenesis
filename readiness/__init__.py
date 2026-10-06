"""Readiness: what a deployment can observe about itself before doing any work.

Three dimensions — machine, interface, account — each answered only by probes a
deployment actually declared, and every undeclared dimension reported as
``not_run``.  Readiness never establishes run acceptance, and a probe failure
closes to ``failed`` instead of guessing.
"""

from readiness.catalog import (
    EXAMPLE_MANIFEST,
    MANIFEST_SCHEMA,
    ReadinessConfigError,
    build_service,
    example_manifest_json,
    load_manifest,
)
from readiness.cli import PublicCliProbe
from readiness.credential import CredentialProbe
from readiness.launch import EnvMode, LaunchPlan, plan_launch
from readiness.local import LocalMachineProbe
from readiness.mcp import AgentMcpProbe
from readiness.service import BOUNDARIES, ReadinessService

__all__ = [
    "BOUNDARIES",
    "EXAMPLE_MANIFEST",
    "MANIFEST_SCHEMA",
    "AgentMcpProbe",
    "CredentialProbe",
    "EnvMode",
    "LaunchPlan",
    "LocalMachineProbe",
    "PublicCliProbe",
    "ReadinessConfigError",
    "ReadinessService",
    "build_service",
    "example_manifest_json",
    "load_manifest",
    "plan_launch",
]
