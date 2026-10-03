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

from orchestration.experiments.backend import (
    ATOMIC_EXPORT_SCOPE_SUPPORTED, ExperimentSession, OpenSandboxBackend, OpenSandboxSession, UnsupportedCapability,
)
from orchestration.experiments.generated import (
    BackendProfile, DockerExportConfiguration, GeneratedContext, GeneratedExperimentPlan, IsolationCapability, IsolationConfiguration,
    IsolationReport, effective_environment,
)
from orchestration.experiments.security import SecurityRejection, verify_isolation
from orchestration.experiments.trusted import IsolationProbeRecord, TrustedProbeRegistry
from orchestration.experiments.frozen_export import FrozenDockerExport

_DENY_ENV = {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


class GeneratedBackend(Protocol):
    @property
    def provenance(self) -> Literal["live", "replay", "mock"]: ...

    capabilities: frozenset[str]

    def isolation(self) -> IsolationReport: ...
    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> ExperimentSession: ...


def declared_capability(*, network_deny: bool, probed_server_process_limit: bool = False,
                        configured_frozen_export: bool = False) -> IsolationCapability:
    """What the pinned OpenSandbox SDK 1.1.0 actually enforces.

    ``SandboxSync.create`` exposes cpu, memory, timeout and an egress
    ``NetworkPolicy`` (deny default), plus container filesystem/credential/host
    isolation. It has no pids/process-limit parameter, so ``process_limit`` is
    declared False (unsupported) and admission fails closed until a backend
    verifies it. Atomic path scope additionally requires the configured trusted
    Docker freeze/archive adapter; ordinary SDK metadata/read is insufficient.
    """
    return IsolationCapability(
        no_host_write=True, no_credentials=True, no_host_control=True, no_privilege=True,
        export_bounded=ATOMIC_EXPORT_SCOPE_SUPPORTED and configured_frozen_export,
        network_deny=network_deny, cpu_limit=True, memory_limit=True,
        process_limit=probed_server_process_limit, time_limit=True, self_owned_cleanup=True,
    )


def registry_with_probe(record: IsolationProbeRecord) -> TrustedProbeRegistry:
    """Host-only helper: register a real (harmless) probe record after it ran."""
    return TrustedProbeRegistry(records=(record,))


class LocalCpuSandboxBackend:
    """Reuses the OpenSandbox SDK lifecycle; isolation stays unverified until a real probe."""

    def __init__(self, *, domain: str = "127.0.0.1:8097", api_key: str | None = None,
                 protocol: Literal["http", "https"] = "http", network_deny: bool = True,
                 probe: IsolationProbeRecord | None = None, instance_id: str | None = None,
                 runtime_profile: str | None = None, server_process_limit: int | None = None,
                 docker_export: DockerExportConfiguration | None = None) -> None:
        self._opensandbox = OpenSandboxBackend(domain=domain, api_key=api_key, protocol=protocol)
        self._network_deny = network_deny
        self._probe = probe
        self._instance_id = instance_id
        self._runtime_profile = runtime_profile
        self._server_process_limit = server_process_limit
        self._docker_export = (DockerExportConfiguration.model_validate_json(docker_export.model_dump_json())
                               if docker_export is not None else None)
        self.provenance: Literal["live"] = "live"
        self.capabilities = self._opensandbox.capabilities

    def isolation(self) -> IsolationReport:
        # SDK 1.1.0 has no process-limit create argument. Only an exact host
        # deployment with a probed server-enforced pids limit can support it.
        config = self._probe.configuration if self._probe is not None else None
        process_supported = bool(self._probe is not None and self._probe.passed and self._probe.verified
            and config is not None and self._server_process_limit is not None
            and config.server_process_limit == self._server_process_limit
            and config.instance_id == self._instance_id and config.runtime_profile == self._runtime_profile
            and config.endpoint == self._endpoint() and config.docker_export == self._docker_export)
        declared = declared_capability(network_deny=self._network_deny,
                                       probed_server_process_limit=process_supported,
                                       configured_frozen_export=self._docker_export is not None)
        verified = (declared.complete and self._probe is not None and self._probe.verified and self._probe.passed)
        reasons = []
        if not declared.export_bounded:
            reasons.append("atomic_export_scope_unsupported")
        if not verified:
            reasons.append("isolation_probe_not_verified")
        return IsolationReport(
            backend="opensandbox", declared=declared,
            verified=verified, probe="passed" if verified else "not_run",
            proof_ref=self._probe.probe_id if self._probe is not None else None,
            reasons=tuple(reasons))

    def _endpoint(self) -> str:
        return self._opensandbox.protocol + "://" + self._opensandbox.domain

    def configuration(self, plan: GeneratedExperimentPlan) -> IsolationConfiguration | None:
        if self._instance_id is None or self._runtime_profile is None:
            return None
        return IsolationConfiguration(
            endpoint=self._endpoint(), instance_id=self._instance_id, runtime_profile=self._runtime_profile,
            environment=effective_environment(plan.environment), resources=plan.backend,
            network_deny=self._network_deny, server_process_limit=self._server_process_limit,
            use_server_proxy=self._opensandbox.use_server_proxy, docker_export=self._docker_export)

    def create(self, plan: GeneratedExperimentPlan, context: GeneratedContext) -> OpenSandboxSession:
        plan = GeneratedExperimentPlan.model_validate_json(plan.model_dump_json())
        if plan.task_id != context.task_id:
            raise SecurityRejection("plan_task_mismatch")
        isolation = self.isolation().model_copy(update={"configuration": self.configuration(plan)})
        registry = TrustedProbeRegistry(records=(self._probe,)) if self._probe is not None else None
        # Independent of the executor: direct SDK adapter callers have the same gate.
        verify_isolation(isolation, registry, plan)
        required = {"script", "cpu", "memory", "duration"}
        if missing := required - self.capabilities:
            raise UnsupportedCapability(",".join(sorted(missing)))
        profile: BackendProfile = plan.backend
        # The immutable image reference is the effective image sent to the SDK;
        # admission already rejected mutable tags. image_digest (if set) is the
        # same digest the host probe ran against and must equal image's digest.
        image = effective_environment(plan.environment).image
        network_policy = NetworkPolicy(defaultAction="deny")
        assert isolation.configuration is not None
        control = FrozenDockerExport(isolation.configuration)
        try:
            control.preflight()  # Read-only exact daemon/service check BEFORE SDK create.
            sandbox = SandboxSync.create(image,
                connection_config=self._opensandbox.connection(profile.command_seconds + 15),
                resource={"cpu": str(profile.cpu), "memory": f"{profile.memory_mib}Mi"},
                timeout=timedelta(seconds=profile.lifetime_seconds), ready_timeout=timedelta(seconds=45),
                entrypoint=["tail", "-f", "/dev/null"], env=_DENY_ENV, network_policy=network_policy,
                metadata={"morph-run": context.run_id, "morph-task": context.task_id,
                          "morph-worker": context.worker_id, "morph-fence": str(context.fencing_token)})
        except BaseException:
            control.close()
            raise
        return OpenSandboxSession(sandbox, owned=True, export_control=control)
