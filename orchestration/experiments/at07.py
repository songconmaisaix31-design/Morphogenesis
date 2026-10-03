"""AT-07 preparation and bounded SDK diagnostics, separate from research execution.

The command-line entry is OFFLINE ONLY. It never opens a connection or mints a
verified probe. The small callable SDK operations below are for the separately
authorized operator procedure in docs/experiments/at07-authorization.md.
"""

from __future__ import annotations

import argparse
from datetime import timedelta
import ipaddress
import json
from pathlib import Path
import re
import time
import tomllib
from typing import Any, Literal, cast

from opensandbox.models.sandboxes import NetworkPolicy
from opensandbox.sync.sandbox import SandboxSync
from pydantic import Field

from contracts.base import Contract
from orchestration.experiments.at07_payloads import PAYLOAD
from orchestration.experiments.backend import ATOMIC_EXPORT_SCOPE_SUPPORTED, OpenSandboxBackend, OpenSandboxSession
from orchestration.experiments.case import PYTHON_IMAGE
from orchestration.experiments.executor import DIRECTORY, _artifact, _write_json, finalize_session
from orchestration.experiments.generated import IsolationConfiguration, effective_environment
from orchestration.experiments.models import ExperimentArtifact
from orchestration.experiments.sandbox_adapter import declared_capability
from orchestration.experiments.frozen_export import FrozenDockerExport
from orchestration.experiments.trusted import IsolationProbeRecord

SERVER_IMAGE = "opensandbox/server:release-1.1.0@sha256:68ca0212a2749b2c73096ce2ec0264455c64442c45f81007db442f52bf84c9d1"
EXECD_IMAGE = "opensandbox/execd:v1.1.0@sha256:6cf7dba2f21f0b536e100563d841ac58a9f31c2b0a081b7ac76796a24d6f47e2"
EGRESS_IMAGE = "opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5"
STEPS = ("filesystem", "network", "cpu", "memory", "pids", "timeout")
CHECKS = ("effective", "host_files", "credentials", "host_control", "privilege", "export",
          "ipv4", "domain", "ipv6", "cpu", "memory", "pids", "command_time", "lifetime", "cleanup")
Status = Literal["passed", "failed", "unsupported", "unknown", "not_run"]


class At07Result(Contract):
    """Diagnostic log only; this is not a scientific result or trust authority."""

    probe_id: str
    configuration: IsolationConfiguration
    provenance: Literal["live", "mock", "replay"]
    sandbox_id: str | None = None
    authorization_ref: str | None = None
    observations: dict[str, Any] = Field(default_factory=dict)
    artifacts: tuple[ExperimentArtifact, ...] = ()
    reasons: tuple[str, ...] = ()
    cleanup_state: Literal["not_created", "destroyed", "unknown"] = "not_created"
    remote_effect: Literal["known", "unknown"] = "unknown"


def validate_configuration(configuration: IsolationConfiguration, server_toml: bytes) -> None:
    c = configuration
    p = c.resources
    if (c.endpoint != "http://127.0.0.1:8099" or not c.use_server_proxy or not c.network_deny
            or c.server_process_limit != 128 or p.cpu != 1 or p.memory_mib != 512
            or p.process_limit != 128 or p.lifetime_seconds != 180 or p.command_seconds != 30
            or p.artifact_bytes != 1048576):
        raise ValueError("at07_fixed_profile_required")
    if c.environment != effective_environment(c.environment) or c.environment.image != PYTHON_IMAGE.replace(":3.12.13-slim", ""):
        raise ValueError("at07_fixed_python_image_required")
    if c.environment.dependencies:
        raise ValueError("at07_stdlib_image_only")
    doc = tomllib.loads(server_toml.decode("utf-8"))
    if (doc.get("runtime") != {"type": "docker", "execd_image": EXECD_IMAGE}
            or doc.get("egress") != {"image": EGRESS_IMAGE, "mode": "dns+nft", "disable_ipv6": True,
                                     "readiness_timeout_seconds": 30.0}
            or doc.get("docker") != {"network_mode": "bridge", "host_ip": "host.docker.internal",
                "port_range_min": 47400, "port_range_max": 47410, "drop_capabilities": ["ALL"],
                "no_new_privileges": True, "pids_limit": 128}
            or doc.get("proxy") != {"resolve_internal": False}
            or doc.get("server") != {"host": "0.0.0.0", "port": 8090}
            or doc.get("ingress") != {"mode": "direct"}
            or doc.get("log") != {"level": "INFO"}
            or set(doc) != {"runtime", "egress", "docker", "proxy", "server", "ingress", "log"}):
        raise ValueError("at07_server_configuration_mismatch")


def render_payload(configuration: IsolationConfiguration, probe_id: str, target_ipv4: str) -> bytes:
    if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", probe_id) is None:
        raise ValueError("invalid_probe_id")
    address = ipaddress.IPv4Address(target_ipv4)
    if not any(address in ipaddress.IPv4Network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")):
        raise ValueError("controlled_private_target_required")
    paths = ["/at07-host-canary/credentials", "/mnt/c/morph-r1/at07/" + probe_id + "/canary/credentials",
             "/run/desktop/mnt/host/c/morph-r1/at07/" + probe_id + "/canary/credentials"]
    p = configuration.resources
    settings = json.dumps({"target_ipv4": str(address), "canary_paths": paths,
        "artifact_bytes": p.artifact_bytes, "memory_mib": p.memory_mib,
        "process_limit": p.process_limit, "command_seconds": p.command_seconds})
    code = PAYLOAD.replace("__SETTINGS__", repr(settings))
    compile(code, "at07-probe.py", "exec")  # Parse only; NEVER exec/eval this on the host.
    return code.encode()


def prepare(configuration: IsolationConfiguration, server_toml: bytes, *, probe_id: str,
            target_ipv4: str, archive_root: Path) -> Path:
    validate_configuration(configuration, server_toml)
    payload = render_payload(configuration, probe_id, target_ipv4)
    root = archive_root.resolve() / probe_id
    root.mkdir(parents=True, exist_ok=False)  # First evidence is never overwritten/replayed.
    _write_json(root / "configuration.json", configuration.model_dump(mode="json"))
    (root / "at07-probe.py").write_bytes(payload)
    (root / "target-ipv4.txt").write_text(target_ipv4, encoding="ascii")
    (root / "server.toml").write_bytes(server_toml)
    _write_json(root / "result.json", At07Result(probe_id=probe_id, configuration=configuration,
        provenance="mock", reasons=("preparation_only_real_probe_NOT_RUN",)).model_dump(mode="json"))
    supported = ATOMIC_EXPORT_SCOPE_SUPPORTED and configuration.docker_export is not None
    _write_json(root / "review.json", {"AT07": "NOT_RUN", "verified": False,
                                      "ready_for_real_at07": supported,
                                      "unsupported_capabilities": [] if supported else ["atomic_bounded_export"],
                                      "checks": dict.fromkeys(CHECKS, "not_run")})
    return root


def create_probe(configuration: IsolationConfiguration, server_toml: bytes, *, probe_id: str,
                 authorization_ref: str, api_key: str, root: Path) -> tuple[OpenSandboxSession, At07Result]:
    """One authorized harmless create; NEVER called by prepare or research factories.

    A durable create-requested record precedes the SDK call. SDK/readiness errors
    leave effect/cleanup unknown; reusing the same directory is refused. Operator
    authorization is external to this module; a reference string is not a grant.
    """
    validate_configuration(configuration, server_toml)
    if not ATOMIC_EXPORT_SCOPE_SUPPORTED or configuration.docker_export is None:
        raise PermissionError("frozen_export_configuration_required")
    if not authorization_ref.strip() or not api_key.strip():
        raise PermissionError("separate_real_probe_authorization_and_service_key_required")
    if re.fullmatch(r"[a-f0-9]{64}", configuration.instance_id) is None or not configuration.runtime_profile.startswith("git:"):
        raise PermissionError("observed_service_instance_and_frozen_runtime_required")
    if root.name != probe_id or not (root / "at07-probe.py").is_file():
        raise ValueError("prepared_probe_required")
    expected = IsolationConfiguration.model_validate_json((root / "configuration.json").read_bytes())
    if expected != configuration or (root / "server.toml").read_bytes() != server_toml:
        raise ValueError("prepared_configuration_changed")
    if (root / "at07-probe.py").read_bytes() != render_payload(configuration, probe_id,
            (root / "target-ipv4.txt").read_text(encoding="ascii")):
        raise ValueError("fixed_probe_source_changed")
    # O_EXCL prevents automatic second POST after crash/disconnect or failure.
    with (root / "create-requested.json").open("x", encoding="utf-8") as f:
        json.dump({"authorization_ref": authorization_ref, "probe_id": probe_id,
                   "remote_effect": "unknown", "requested_at": time.time()}, f)
    result = At07Result(probe_id=probe_id, configuration=configuration, provenance="live",
        authorization_ref=authorization_ref, cleanup_state="unknown")
    _write_json(root / "result.json", result.model_dump(mode="json"))
    backend = OpenSandboxBackend(domain="127.0.0.1:8099", api_key=api_key)
    p = configuration.resources
    control: FrozenDockerExport | None = None
    try:
        control = FrozenDockerExport(configuration)
        control.preflight()
        sandbox = SandboxSync.create(configuration.environment.image,
            connection_config=backend.connection(p.command_seconds + 15),
            timeout=timedelta(seconds=p.lifetime_seconds), ready_timeout=timedelta(seconds=45),
            resource={"cpu": str(p.cpu), "memory": f"{p.memory_mib}Mi"},
            entrypoint=["tail", "-f", "/dev/null"], network_policy=NetworkPolicy(defaultAction="deny"),
            env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
            metadata={"morph-at07-probe": probe_id})
    except Exception as error:
        if control is not None:
            control.close()
        result = result.model_copy(update={"reasons": ("create_unknown_" + type(error).__name__,)})
        _write_json(root / "result.json", result.model_dump(mode="json"))
        raise
    session = OpenSandboxSession(sandbox, owned=True, export_control=control)
    result = result.model_copy(update={"sandbox_id": session.id})
    _write_json(root / "result.json", result.model_dump(mode="json"))
    return session, result


def run_step(session: OpenSandboxSession, result: At07Result, root: Path, step: str) -> At07Result:
    """A single fixed step, with original SDK execution/log/status preserved."""
    if not session.owned or result.sandbox_id != session.id or result.provenance != "live":
        raise PermissionError("fresh_owned_live_probe_required")
    if step not in STEPS or step in result.observations:
        raise ValueError("unknown_or_repeated_probe_step")
    created = json.loads((root / "create-requested.json").read_bytes())["requested_at"]
    if not 0 <= time.time() - created < 240:
        raise TimeoutError("at07_total_command_window_expired")
    index = STEPS.index(step)
    if any(name not in result.observations for name in STEPS[:index]):
        raise ValueError("probe_order_required")
    for name in STEPS[:index]:
        previous = result.observations[name]
        if previous.get("exit_code") != 0 or previous.get("error") is not None:
            raise PermissionError("previous_probe_did_not_complete_stop_required")
    path = root / (step + "-requested.json")
    with path.open("x", encoding="utf-8") as f:
        json.dump({"step": step, "remote_effect": "unknown"}, f)
    if step == "filesystem":
        payload = render_payload(result.configuration, result.probe_id,
                                 (root / "target-ipv4.txt").read_text(encoding="ascii"))
        if (root / "at07-probe.py").read_bytes() != payload:
            raise ValueError("fixed_probe_source_changed")
        session.upload(DIRECTORY + "/at07-probe.py", payload)
    seconds = result.configuration.resources.command_seconds if step == "timeout" else 15
    started = time.monotonic()
    execution = session.run(["python3", DIRECTORY + "/at07-probe.py", step], seconds, DIRECTORY)
    raw = execution.model_dump_json().encode()
    observation: dict[str, Any] = {"exit_code": execution.exit_code, "command_id": execution.id,
        "elapsed": time.monotonic() - started, "error": execution.error.model_dump(mode="json") if execution.error else None}
    stdout = "".join(log.text for log in execution.logs.stdout)
    if len(raw) > 65536 or len(stdout) > 16384:
        raise ValueError("probe_log_limit")
    artifact = _artifact(root, step + "-command.json", raw)
    if step == "timeout":
        observation["status"] = session.command_status(execution.id) if execution.id else None
    elif execution.exit_code == 0 and execution.error is None:
        observation["data"] = json.loads(stdout)
    observations = {**result.observations, step: observation}
    result = result.model_copy(update={"observations": observations, "artifacts": (*result.artifacts, artifact)})
    _write_json(root / "result.json", result.model_dump(mode="json"))
    return result


def check_exports(session: OpenSandboxSession, result: At07Result, root: Path) -> At07Result:
    if not session.owned or session.id != result.sandbox_id:
        raise PermissionError("fresh_owned_probe_required")
    with (root / "export-requested.json").open("x", encoding="utf-8") as f:
        json.dump({"remote_effect": "unknown"}, f)
    observations: dict[str, Any] = {"small": session.download(DIRECTORY + "/at07-small.bin", 64) == b"AT07-safe-export"}
    control = session.export_control
    observations["frozen_export"] = control is not None and bool(control.observations)
    if control is not None:
        _write_json(root / "frozen-export.json", control.observations)
    for label, name, limit in (("large", DIRECTORY + "/at07-large.bin", 1048576),
            ("absolute", "/tmp/at07-outside.txt", 64),
            ("traversal", DIRECTORY + "/../at07-outside.txt", 64),
            ("symlink", DIRECTORY + "/at07-link.bin", 64)):
        try:
            session.download(name, limit)
            observations[label] = "allowed"
        except (ValueError, PermissionError) as error:
            observations[label] = str(error)
        except Exception as error:
            observations[label] = "unknown:" + type(error).__name__
    result = result.model_copy(update={"observations": {**result.observations, "export": observations}})
    _write_json(root / "result.json", result.model_dump(mode="json"))
    return result


def finish(session: OpenSandboxSession | None, result: At07Result, root: Path) -> At07Result:
    """The original cleanup path; never accept an attached or mismatched ID."""
    if session is not None and (not session.owned or session.id != result.sandbox_id):
        raise PermissionError("cleanup_owned_identity_mismatch")
    return cast(At07Result, finalize_session(result, root, list(result.artifacts), session))


def review(result: At07Result) -> dict[str, Status]:
    """Conservative diagnostics. Mock/replay, missing facts and unknown stay so.

    Host observations below must come from the operator's own live inspection,
    canaries and raw logs. This function is NOT registry admission/attestation.
    """
    checks: dict[str, Status] = dict.fromkeys(CHECKS, "unknown")
    if result.provenance != "live" or result.sandbox_id is None:
        return dict.fromkeys(CHECKS, "not_run")
    o = result.observations

    def decide(name: str, condition: bool) -> None:
        checks[name] = "passed" if condition else "failed"

    def requires(name: str, keys: tuple[str, ...]) -> None:
        if any(host.get(key) is None for key in keys):
            checks[name] = "unknown"

    host = o.get("host", {})
    for name, key in (("effective", "effective_configuration_matches"), ("lifetime", "expiry_observed")):
        if key in host:
            decide(name, host[key] is True)
    f = o.get("filesystem", {}).get("data", {})
    if f:
        access = f.get("access", [])
        decide("host_files", len(access) == 3 and all(x.get("read") in (2, 13) and x.get("write") in (2, 13) for x in access)
               and host.get("canary_unchanged") is True and host.get("canary_positive_control") is True)
        decide("credentials", f.get("fake_credential_visible") is False and host.get("fake_credential_control") is True)
        decide("host_control", f.get("control_sockets") == [] and host.get("no_host_mounts_or_control") is True)
        privilege = f.get("privilege", {})
        decide("privilege", privilege.get("NoNewPrivs") == "1" and privilege.get("CapEff") == "0000000000000000"
               and privilege.get("CapBnd") == "0000000000000000" and privilege.get("raw_socket") in (1, 13)
               and privilege.get("unshare") == -1 and privilege.get("unshare_errno") in (1, 13))
        requires("host_files", ("canary_unchanged", "canary_positive_control"))
        requires("credentials", ("fake_credential_control",))
        requires("host_control", ("no_host_mounts_or_control",))
        if any(x.get("read") == "accessible" or x.get("write") == "accessible" for x in access):
            checks["host_files"] = "failed"
        if f.get("fake_credential_visible") is True:
            checks["credentials"] = "failed"
        if f.get("control_sockets"):
            checks["host_control"] = "failed"
    if "export" in o:
        e = o["export"]
        decide("export", e.get("small") is True and e.get("large") == "artifact_size_limit"
               and all(e.get(n) == "artifact_path_escape" for n in ("absolute", "traversal"))
               and e.get("symlink") in {"artifact_path_escape", "artifact_path_escape_or_type"})
    n = o.get("network", {}).get("data", {})
    if n:
        controlled = host.get("target_positive_before_and_after") is True and host.get("no_denied_target_hits") is True
        decide("ipv4", n.get("direct_ipv4") in ("timeout", 1, 13) and controlled
               and host.get("effective_nft_default_deny") is True)
        decide("domain", n.get("domain") == {"id": 1707, "rcode": 3, "answers": 0} and controlled
               and host.get("target_dns_positive") is True and host.get("egress_domain_denial_observed") is True)
        decide("ipv6", n.get("ipv6_disabled") == {"all": "1", "default": "1", "lo": "1"}
               and n.get("ipv6_bind") in (97, 99))
        requires("ipv4", ("target_positive_before_and_after", "no_denied_target_hits", "effective_nft_default_deny"))
        requires("domain", ("target_positive_before_and_after", "no_denied_target_hits", "target_dns_positive", "egress_domain_denial_observed"))
        if n.get("direct_ipv4") == "connected":
            checks["ipv4"] = "failed"
        if n.get("domain", {}).get("answers", 0) > 0:
            checks["domain"] = "failed"
    for name, file, counter in (("cpu", "cpu.max", "nr_throttled"), ("memory", "memory.max", "max"), ("pids", "pids.max", "max")):
        data = o.get(name, {}).get("data", {})
        if data:
            expected = {"memory": "536870912", "pids": "128"}.get(name)
            limit = data.get("limits", {}).get(file)
            if name == "cpu":
                parts = str(limit).split()
                matches = len(parts) == 2 and parts[0].isdigit() and int(parts[0]) > 0 and parts[0] == parts[1]
            else:
                matches = limit == expected
            before, after = data.get("before", {}).get(counter), data.get("after", {}).get(counter)
            increased = type(before) is int and type(after) is int and after > before
            decide(name, matches and increased and (name != "pids" or data.get("fork_errno") == 11))
    t = o.get("timeout", {})
    if t:
        error = t.get("error") or {}
        decide("command_time", error.get("name") in ("TimeoutError", "CommandTimeout", "DeadlineExceeded")
               and (t.get("status") or {}).get("running") is False
               and 28 <= t.get("elapsed", 0) <= 45 and host.get("timeout_marker_absent") is True)
        requires("command_time", ("timeout_marker_absent",))
        if (t.get("exit_code") == 0 and not t.get("error")) or (t.get("status") or {}).get("running") is True:
            checks["command_time"] = "failed"
    if "cleanup_observed" in host:
        decide("cleanup", result.cleanup_state == "destroyed" and host["cleanup_observed"] is True
               and host.get("unrelated_resources_unchanged") is True)
        requires("cleanup", ("unrelated_resources_unchanged",))
    for name in host.get("unsupported", []):
        if name in checks:
            checks[name] = "unsupported"
    if result.remote_effect != "known":
        checks["cleanup"] = "unknown"
    if checks["export"] == "passed":
        if not ATOMIC_EXPORT_SCOPE_SUPPORTED or result.configuration.docker_export is None:
            checks["export"] = "unsupported"
        elif o.get("export", {}).get("frozen_export") is not True:
            checks["export"] = "unknown"
    return checks


def unverified_record(result: At07Result, evidence_ref: str) -> IsolationProbeRecord:
    """Preparation/static review can never produce authority for live execution."""
    return IsolationProbeRecord(probe_id=result.probe_id, backend="opensandbox",
        declared=declared_capability(network_deny=True).model_copy(update={"export_bounded": False}),
        image_digest=result.configuration.environment.image_digest,
        verified=False, passed=False, evidence_ref=evidence_ref, probed_at=0,
        configuration=result.configuration)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    prep = sub.add_parser("prepare", help="offline: configuration + fixed probe source + NOT_RUN report")
    prep.add_argument("--configuration", required=True, type=Path)
    prep.add_argument("--server-config", required=True, type=Path)
    prep.add_argument("--probe-id", required=True)
    prep.add_argument("--target-ipv4", required=True)
    prep.add_argument("--archive-root", required=True, type=Path)
    read = sub.add_parser("review", help="offline diagnostic; never registers a verified probe")
    read.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    if args.operation == "prepare":
        config = IsolationConfiguration.model_validate_json(args.configuration.read_bytes())
        root = prepare(config, args.server_config.read_bytes(), probe_id=args.probe_id,
                       target_ipv4=args.target_ipv4, archive_root=args.archive_root)
        print(json.dumps({"path": str(root), "AT07": "NOT_RUN", "verified": False,
                          "ready_for_real_at07": False, "unsupported_capabilities": ["atomic_bounded_export"]}))
    else:
        result = At07Result.model_validate_json(args.result.read_bytes())
        print(json.dumps({"checks": review(result), "verified": False, "registry_written": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
