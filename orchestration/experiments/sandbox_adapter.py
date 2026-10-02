"""Local CPU isolation adapter for generated candidates.

This is the R1 "local CPU usable isolation path": a thin configuration and
check in front of the existing OpenSandbox backend. It does not build a second
scheduler. The adapter *declares* the isolation properties the local Linux
OpenSandbox service is configured to enforce, and claims a ``proof_ref`` when a
real harmless probe has been recorded.

Authorization is host-owned: ``IsolationReport.verified``/``probe`` are advisory
and the executor ignores them. Admission requires a ``TrustedProbeRegistry``
entry whose ``declared`` capability set matches this adapter's declaration and
whose probe ``passed``. This round no real probe is authorized, so generated
candidates fail closed rather than running on the host.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Literal, Protocol

from opensandbox.models.sandboxes import NetworkPolicy
from opensandbox.sync.sandbox import SandboxSync

from orchestration.experiments.backend import OpenSandboxBackend, OpenSandboxSession, UnsupportedCapability
from orchestration.experiments.generated import (
    BackendProfile, GeneratedContext, GeneratedExperimentPlan, IsolationCapability, IsolationReport,
)
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry

_DENY_ENV = {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


class GeneratedBackend(Protocol):
    provenance: Literal["live", "replay", "mock"]
    capabilities: frozenset[str]

    def isolation(self) -> IsolationReport: ...
    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> OpenSandboxSession: ...


def declared_capability(*, network_deny: bool) -> IsolationCapability:
    """What the pinned OpenSandbox SDK 1.1.0 actually enforces.

    ``SandboxSync.create`` exposes cpu, memory, timeout and an egress
    ``NetworkPolicy`` (deny default), plus container filesystem/credential/host
    isolation. It has no pids/process-limit parameter, so ``process_limit`` is
    declared False (unsupported) and admission fails closed until a backend
    verifies it. Never inflate a claim into a proof.
    """
    return IsolationCapability(
        no_host_write=True, no_credentials=True, no_host_control=True, no_privilege=True,
        export_bounded=True, network_deny=network_deny, cpu_limit=True, memory_limit=True,
        process_limit=False, time_limit=True, self_owned_cleanup=True,
    )


def registry_with_probe(record: IsolationProbeRecord) -> TrustedProbeRegistry:
    """Host-only helper: register a real (harmless) probe record after it ran."""
    return TrustedProbeRegistry(records=(record,))


class LocalCpuSandboxBackend:
    """Reuses the OpenSandbox SDK lifecycle; isolation stays unverified until a real probe."""

    def __init__(self, *, domain: str = "127.0.0.1:8097", api_key: str | None = None,
                 protocol: Literal["http", "https"] = "http", network_deny: bool = True,
                 probe: IsolationProbeRecord | None = None) -> None:
        self._opensandbox = OpenSandboxBackend(domain=domain, api_key=api_key, protocol=protocol)
        self._network_deny = network_deny
        self._probe = probe
        self.provenance: Literal["live"] = "live"
        self.capabilities = self._opensandbox.capabilities

    def isolation(self) -> IsolationReport:
        declared = declared_capability(network_deny=self._network_deny)
        verified = self._probe is not None and self._probe.verified and self._probe.passed
        return IsolationReport(
            backend="opensandbox", declared=declared,
            verified=verified, probe="passed" if verified else "not_run",
            proof_ref=self._probe.probe_id if self._probe is not None else None,
            reasons=() if verified else ("isolation_probe_not_run",))

    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> OpenSandboxSession:
        required = {"script", "cpu", "memory", "duration"}
        if missing := required - self.capabilities:
            raise UnsupportedCapability(",".join(sorted(missing)))
        profile: BackendProfile = plan.backend
        # The immutable image reference is the effective image sent to the SDK;
        # admission already rejected mutable tags. image_digest (if set) is the
        # same digest the host probe ran against and must equal image's digest.
        image = plan.environment.image
        if plan.environment.image_digest and not image.endswith("@" + plan.environment.image_digest):
            raise UnsupportedCapability("image_digest_mismatch")
        network_policy = NetworkPolicy(defaultAction="deny") if self._network_deny else None
        sandbox = SandboxSync.create(image,
            connection_config=self._opensandbox.connection(profile.command_seconds + 15),
            resource={"cpu": str(profile.cpu), "memory": f"{profile.memory_mib}Mi"},
            timeout=timedelta(seconds=profile.lifetime_seconds), ready_timeout=timedelta(seconds=45),
            entrypoint=["tail", "-f", "/dev/null"], env=_DENY_ENV, network_policy=network_policy,
            metadata={"morph-run": context.run_id, "morph-task": context.task_id,
                      "morph-worker": context.worker_id, "morph-fence": str(context.fencing_token)})
        return OpenSandboxSession(sandbox, owned=True)
