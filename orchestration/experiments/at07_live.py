"""Separately authorized AT-07 operator procedure. NOT run by preparation/tests.

No service startup, pulls, Docker mutations, research candidates or registry
writes. The only mutations are one official SDK sandbox create, fixed diagnostics
inside that owned sandbox, and the original SDK cleanup path.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import time
from typing import Any

from opensandbox.exceptions import SandboxApiException

from orchestration.experiments.at07 import (
    At07Result, CHECKS, EGRESS_IMAGE, SERVER_IMAGE, STEPS, check_exports, create_probe,
    finish, render_payload, review, run_step, validate_configuration,
)
from orchestration.experiments.backend import ATOMIC_EXPORT_SCOPE_SUPPORTED, OpenSandboxSession, UnsupportedCapability
from orchestration.experiments.case import PYTHON_IMAGE
from orchestration.experiments.executor import _write_json
from orchestration.experiments.generated import IsolationConfiguration

# Only these non-secret Docker fields enter the evidence. Never inspect Config.Env,
# arbitrary labels (the egress auth token is a label), or expanded Compose output.
INSPECT = r'''{"id":{{json .Id}},"image":{{json .Config.Image}},"state":{{json .State.Status}},"owner":{{json (index .Config.Labels "morph.owner")}},"probe":{{json (index .Config.Labels "morph-at07-probe")}},"sidecar_for":{{json (index .Config.Labels "opensandbox.io/egress-sidecar-for")}},"privileged":{{json .HostConfig.Privileged}},"cpu":{{json .HostConfig.NanoCpus}},"memory":{{json .HostConfig.Memory}},"pids":{{json .HostConfig.PidsLimit}},"caps_drop":{{json .HostConfig.CapDrop}},"caps_add":{{json .HostConfig.CapAdd}},"security":{{json .HostConfig.SecurityOpt}},"network":{{json .HostConfig.NetworkMode}},"mounts":{{json .Mounts}},"ports":{{json .NetworkSettings.Ports}},"ip":{{json .NetworkSettings.IPAddress}}}'''


def docker_read(*args: str) -> str:
    allowed = (("inspect",), ("ps",), ("volume", "ls"), ("network", "ls"), ("logs",))
    fixed_exec = (len(args) >= 3 and args[0] == "exec" and re.fullmatch(r"[a-f0-9]{64}", args[1]) is not None
        and args[2:] in (("cat", "/etc/opensandbox/config.toml"), ("nft", "-j", "list", "ruleset")))
    if not fixed_exec and not any(args[:len(prefix)] == prefix for prefix in allowed):
        raise PermissionError("docker_read_only")
    completed = subprocess.run(["docker", *args], capture_output=True, text=True,
                               timeout=10, check=False)
    if completed.returncode != 0:
        raise RuntimeError("docker_read_failed")  # Do not leak stderr/environment.
    # Docker log streams can arrive on stderr even with exit status zero. They
    # remain in memory until the caller selects the fixed synthetic-domain lines.
    output = completed.stdout + completed.stderr if args[0] == "logs" else completed.stdout
    if len(output) > 262144:
        raise ValueError("docker_observation_limit")
    return output.strip()


def inspect(identifier: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(docker_read("inspect", "--format", INSPECT, identifier))
    return value


def inventory() -> dict[str, list[str]]:
    return {"containers": sorted(docker_read("ps", "-aq", "--no-trunc").splitlines()),
            "volumes": sorted(docker_read("volume", "ls", "-q").splitlines()),
            "networks": sorted(docker_read("network", "ls", "-q", "--no-trunc").splitlines())}


def target_control() -> dict[str, Any]:
    with socket.create_connection(("127.0.0.1", 8098), timeout=2) as tcp:
        tcp.sendall(b"AT07-CONTROL\n")
        raw = tcp.recv(2048)
    result: dict[str, Any] = json.loads(raw)
    question = b"\x06canary\x04at07\x04test\0\0\x01\0\x01"
    query = struct.pack("!HHHHHH", 1707, 0x0100, 1, 0, 0, 0) + question
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dns:
        dns.settimeout(2)
        dns.sendto(query, ("127.0.0.1", 8053))
        answer, _ = dns.recvfrom(512)
    result["dns_positive"] = (len(answer) >= 12 and answer[:2] == query[:2]
        and answer[3] & 15 == 0 and struct.unpack("!H", answer[6:8])[0] == 1)
    return result


def effective(main: dict[str, Any], sidecar: dict[str, Any], result: At07Result) -> bool:
    """Actual Docker settings, not the SDK create arguments."""
    mount = main.get("mounts", [])
    expected_volume = "opensandbox-runtime-" + str(result.sandbox_id)
    return (main.get("probe") == result.probe_id and main.get("image") == result.configuration.environment.image
        and main.get("privileged") is False and main.get("cpu") == 1000000000
        and main.get("memory") == 536870912 and main.get("pids") == 128
        and "ALL" in (main.get("caps_drop") or []) and not main.get("caps_add")
        and any(s in ("no-new-privileges", "no-new-privileges=true") for s in (main.get("security") or []))
        and main.get("network") == "container:" + str(sidecar.get("id"))
        and len(mount) == 1 and mount[0].get("Type") == "volume"
        and mount[0].get("Name") == expected_volume and mount[0].get("Destination") == "/opt/opensandbox"
        and sidecar.get("sidecar_for") == result.sandbox_id and sidecar.get("image") == EGRESS_IMAGE
        and sidecar.get("privileged") is False and sidecar.get("network") == "bridge")


def execute(*, root: Path, authorization_ref: str, key_file: Path, canary_directory: Path,
            accept_infrastructure_limits: bool = False) -> At07Result:
    """One probe, max 300 s after create-request; any uncertain mutation stops.

    Infrastructure limitations are disclosed in the authorization package. The
    pinned Docker server leaves sidecar resource limits unset and publishes its
    ports on 0.0.0.0. An explicit scope decision is mandatory; this switch cannot
    grant AT-07 PASS and does not change any settings or relax a probe criterion.
    """
    if not authorization_ref.strip() or not accept_infrastructure_limits:
        raise PermissionError("separate_authorization_and_infrastructure_scope_decision_required")
    if not ATOMIC_EXPORT_SCOPE_SUPPORTED:
        raise UnsupportedCapability("atomic_export_scope_unsupported_AT07_NOT_READY")
    if (root / "create-requested.json").exists():
        raise FileExistsError("original_probe_is_not_replayable")
    config = IsolationConfiguration.model_validate_json((root / "configuration.json").read_bytes())
    server_toml = (root / "server.toml").read_bytes()
    validate_configuration(config, server_toml)
    server, target = inspect("morph-r1-at07-server"), inspect("morph-r1-at07-target")
    if (server["id"] != config.instance_id or server["image"] != SERVER_IMAGE
            or server["owner"] != "r1-at07" or target["owner"] != "r1-at07"
            or target["image"] != PYTHON_IMAGE
            or server["state"] != "running" or target["state"] != "running"):
        raise PermissionError("owned_service_instance_required")
    actual_server = docker_read("exec", server["id"], "cat", "/etc/opensandbox/config.toml").encode()
    validate_configuration(config, actual_server)
    target_ip = (root / "target-ipv4.txt").read_text(encoding="ascii")
    if target["ip"] != target_ip or (root / "at07-probe.py").read_bytes() != render_payload(config, root.name, target_ip):
        raise ValueError("prepared_target_or_probe_changed")
    canary = canary_directory / "credentials"
    if canary.is_symlink() or canary.read_bytes() != b"AT07-SYNTHETIC-NOT-A-SECRET\n":
        raise ValueError("new_synthetic_canary_required")
    before = inventory()
    positive = target_control()
    if not all(positive.get(k) is True for k in ("dns_positive", "canary_exists", "fake_credential_present")):
        raise ValueError("controlled_target_positive_failed")
    _write_json(root / "host-before.json", {"inventory": before, "server": server, "target": target,
                "positive": positive, "infrastructure_limits_explicitly_accepted": True})
    session: OpenSandboxSession | None = None
    result = At07Result(probe_id=root.name, configuration=config, provenance="live")
    ids: set[str] = set()
    volume = ""
    host: dict[str, Any] = {}
    expired = False
    started = time.monotonic()
    try:
        session, result = create_probe(config, server_toml, probe_id=root.name,
            authorization_ref=authorization_ref, api_key=key_file.read_text(encoding="utf-8").strip(), root=root)
        info = session.info()
        _write_json(root / "sdk-info.json", {k: info.get(k) for k in
            ("id", "state", "created_at", "createdAt", "expires_at", "expiresAt")})
        main = inspect("sandbox-" + session.id)
        sidecars = docker_read("ps", "-aq", "--no-trunc", "--filter",
                              "label=opensandbox.io/egress-sidecar-for=" + session.id).splitlines()
        if len(sidecars) != 1:
            raise ValueError("unique_owned_sidecar_missing")
        sidecar = inspect(sidecars[0])
        ids = {main["id"], sidecar["id"]}
        volume = "opensandbox-runtime-" + session.id
        _write_json(root / "owned-resources.json", {"main": main, "sidecar": sidecar, "volume": volume})
        host["effective_configuration_matches"] = effective(main, sidecar, result)
        host["no_host_mounts_or_control"] = host["effective_configuration_matches"]
        if not host["effective_configuration_matches"]:
            raise ValueError("actual_configuration_mismatch_stop")
        policy = session.sandbox.get_egress_policy().model_dump(mode="json")
        _write_json(root / "effective-policy.json", policy)
        if policy.get("default_action") != "deny" or policy.get("egress") not in (None, []):
            raise ValueError("effective_network_policy_not_default_deny")
        nft = json.loads(docker_read("exec", sidecar["id"], "nft", "-j", "list", "ruleset"))
        _write_json(root / "effective-nft.json", nft)
        host["effective_nft_default_deny"] = any(
            rule.get("chain", {}).get("hook") == "output" and rule["chain"].get("type") == "filter"
            and rule["chain"].get("policy") == "drop" for rule in nft.get("nftables", []))
        if not host["effective_nft_default_deny"]:
            raise ValueError("actual_nft_default_drop_missing")
        host["canary_positive_control"] = True
        host["fake_credential_control"] = True
        result = result.model_copy(update={"observations": {"host": host}})
        for step in STEPS:
            if time.monotonic() - started > 210:
                raise TimeoutError("probe_total_deadline")
            result = run_step(session, result, root, step)
            if step == "filesystem":
                host["canary_unchanged"] = canary.read_bytes() == b"AT07-SYNTHETIC-NOT-A-SECRET\n"
                result = check_exports(session, result, root)
                if review(result)["export"] != "passed":
                    raise ValueError("export_probe_failed_stop")
            if step == "network":
                after_control = target_control()
                _write_json(root / "target-after.json", after_control)
                host["target_positive_before_and_after"] = after_control.get("canary_exists") is True
                host["target_dns_positive"] = positive["dns_positive"] is True and after_control.get("dns_positive") is True
                host["no_denied_target_hits"] = (after_control["denied_tcp_hits"] == positive["denied_tcp_hits"] == 0
                    and after_control["dns_queries"] == positive["dns_queries"] + 1)
                # Retain only the fixed synthetic domain's log lines, never a
                # complete infrastructure log, environment or token-bearing labels.
                logs = docker_read("logs", "--tail", "100", sidecar["id"])
                lines = [line[:2048] for line in logs.splitlines() if "canary.at07.test" in line]
                (root / "domain-denial.log").write_text("\n".join(lines), encoding="utf-8")
                host["egress_domain_denial_observed"] = True if any(re.search(
                    r'action["\s]*[:=]["\s]*deny\b', line, re.IGNORECASE) for line in lines) else None
            if step == "timeout":
                session.info()  # 404 for a dead sandbox must not pass a file-negative.
                try:
                    session.sandbox.files.get_file_info(["/tmp/morph-research/at07-timeout-completed"])
                    host["timeout_marker_absent"] = False
                except SandboxApiException as error:
                    if error.status_code != 404:
                        raise
                    session.info()
                    host["timeout_marker_absent"] = True
                _write_json(root / "timeout-marker.json", {"absent": host["timeout_marker_absent"]})
            result = result.model_copy(update={"observations": {**result.observations, "host": host}})
            observation = result.observations[step]
            if step != "timeout" and (observation.get("exit_code") != 0 or observation.get("error") is not None):
                raise ValueError("probe_did_not_complete_stop")
            if "failed" in review(result).values():
                raise ValueError("negative_probe_failed_stop")
        host["canary_unchanged"] = canary.read_bytes() == b"AT07-SYNTHETIC-NOT-A-SECRET\n"
        # The SDK supplies the server expiry; neither wall time nor a kill request
        # alone proves automatic expiry. Observe actual owned Docker IDs disappear.
        expiry_text = info.get("expires_at") or info.get("expiresAt")
        expiry = datetime.fromisoformat(str(expiry_text).replace("Z", "+00:00")).timestamp()
        while time.monotonic() - started < 240:
            present = set(inventory()["containers"])
            if not ids & present:
                expired = time.time() >= expiry and volume not in inventory()["volumes"]
                break
            if time.time() >= expiry + 20:
                break
            time.sleep(1)
        host["expiry_observed"] = expired
        if expired:
            # Already absent; never issue a DELETE for a different/recovered ID.
            session.close()
            session = None
            result = result.model_copy(update={"cleanup_state": "destroyed"})
        result = result.model_copy(update={"remote_effect": "known"})
    except Exception as error:
        result = result.model_copy(update={"reasons": (*result.reasons, type(error).__name__), "remote_effect": "unknown"})
        # create_probe persisted the unknown create fact before POST, including
        # any SDK exception. Do not erase its unresolved identity/cleanup state.
        if session is None and (root / "create-requested.json").exists():
            saved = At07Result.model_validate_json((root / "result.json").read_bytes())
            result = saved.model_copy(update={"reasons": (*saved.reasons, *result.reasons, "create_or_readiness_unknown"),
                                              "remote_effect": "unknown"})
    finally:
        result = result.model_copy(update={"observations": {**result.observations, "host": host}})
        result = finish(session, result, root)
        try:
            after = inventory()
            _write_json(root / "host-after.json", after)
            host["cleanup_observed"] = bool(ids) and not ids & set(after["containers"]) and volume not in after["volumes"]
            host["unrelated_resources_unchanged"] = all(set(before[k]) <= set(after[k]) for k in before)
        except Exception:
            host["cleanup_observed"] = None
        result = result.model_copy(update={"observations": {**result.observations, "host": host}})
        _write_json(root / "result.json", result.model_dump(mode="json"))
        _write_json(root / "review.json", {"checks": review(result), "verified": False, "registry_written": False,
            "pending_host_review": [k for k in ("effective_nft_default_deny", "egress_domain_denial_observed", "timeout_marker_absent")
                                    if host.get(k) is not True]})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-separately-authorized-probe", action="store_true", required=True)
    parser.add_argument("--authorization-ref", required=True)
    parser.add_argument("--accept-disclosed-infrastructure-limits", action="store_true")
    parser.add_argument("--prepared-root", required=True, type=Path)
    parser.add_argument("--service-key-file", required=True, type=Path)
    parser.add_argument("--canary-directory", required=True, type=Path)
    args = parser.parse_args()
    result = execute(root=args.prepared_root.resolve(), authorization_ref=args.authorization_ref,
        key_file=args.service_key_file, canary_directory=args.canary_directory,
        accept_infrastructure_limits=args.accept_disclosed_infrastructure_limits)
    checks = review(result)
    print(json.dumps({"probe_id": result.probe_id, "checks": checks, "verified": False, "registry_written": False}))
    return 0 if all(checks[n] == "passed" for n in CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
