"""AT07 preparation/decision tests. All sandbox, process and network I/O denied."""

import ast
import json
import os
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from orchestration.experiments import at07
from orchestration.experiments import at07_live
from orchestration.experiments.backend import OpenSandboxSession
from orchestration.experiments.case import PYTHON_IMAGE
from orchestration.experiments.generated import ApprovedEnvironment, BackendProfile, IsolationConfiguration, IsolationReport, effective_environment
from orchestration.experiments.trusted import TrustedProbeRegistry

CONFIG = Path(__file__).resolve().parents[2] / "deploy/opensandbox/at07.config.toml"


@pytest.fixture(autouse=True)
def denied_execution(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("offline AT07 cannot run a process, probe or network request")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket.socket, "sendto", denied)
    monkeypatch.setattr(at07.SandboxSync, "create", denied)


def configuration():
    return IsolationConfiguration(endpoint="http://127.0.0.1:8099", instance_id="1" * 64,
        runtime_profile="git:" + "a" * 40 + ":deploy/opensandbox/at07.config.toml",
        environment=effective_environment(ApprovedEnvironment(image=PYTHON_IMAGE, dependency_lock_sha256="0" * 64)),
        resources=BackendProfile(process_limit=128), network_deny=True, server_process_limit=128)


def prepared(tmp_path):
    return at07.prepare(configuration(), CONFIG.read_bytes(), probe_id="fixture", target_ipv4="172.17.0.2", archive_root=tmp_path)


def test_prepare_only_parses_program_and_preserves_first_directory(tmp_path):
    root = prepared(tmp_path)
    code = (root / "at07-probe.py").read_text()
    ast.parse(code)
    assert "__SETTINGS__" not in code and "172.17.0.2" in code
    assert 'range(SETTINGS["process_limit"] + 1)' in code
    assert "os.kill(pid, signal.SIGKILL)" in code and "killpg" not in code
    result = at07.At07Result.model_validate_json((root / "result.json").read_bytes())
    assert set(at07.review(result).values()) == {"not_run"}
    assert not at07.unverified_record(result, "fixture").verified
    with pytest.raises(FileExistsError):
        prepared(tmp_path)


@pytest.mark.parametrize("ip", ["8.8.8.8", "127.0.0.1", "169.254.169.254", "::1", "example.com"])
def test_only_explicit_controlled_private_destination(ip):
    with pytest.raises(ValueError):
        at07.render_payload(configuration(), "fixture", ip)


@pytest.mark.parametrize("old,new", [
    ('mode = "dns+nft"', 'mode = "dns"'), ('disable_ipv6 = true', 'disable_ipv6 = false'),
    ('drop_capabilities = ["ALL"]', 'drop_capabilities = []'), ('pids_limit = 128', 'pids_limit = 1024'),
    ('no_new_privileges = true', 'no_new_privileges = false'), ('network_mode = "bridge"', 'network_mode = "host"'),
    (at07.EGRESS_IMAGE, "opensandbox/egress:latest"),
])
def test_misconfiguration_refused_offline(old, new):
    with pytest.raises(ValueError, match="configuration_mismatch"):
        at07.validate_configuration(configuration(), CONFIG.read_bytes().replace(old.encode(), new.encode()))


def test_sdk_probe_create_is_one_official_bounded_deny_request(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    calls = []
    def capture(image, **options):
        calls.append((image, options))
        return SimpleNamespace(id="inert-sdk-id")
    monkeypatch.setattr(at07.SandboxSync, "create", capture)
    session, result = at07.create_probe(configuration(), CONFIG.read_bytes(), probe_id="fixture",
        authorization_ref="inert-test-reference-not-authorization", api_key="fake-key", root=root)
    assert session.id == result.sandbox_id == "inert-sdk-id" and len(calls) == 1
    image, request = calls[0]
    assert image == configuration().environment.image
    assert request["network_policy"].default_action == "deny"
    assert request["resource"] == {"cpu": "1", "memory": "512Mi"}
    assert request["timeout"].total_seconds() == 180
    assert request["connection_config"].retry_policy.max_retries == 0
    assert request["connection_config"].use_server_proxy is True
    assert not {"volumes", "extensions", "credential_proxy"} & request.keys()
    assert not at07.unverified_record(result, "inert-interception").verified
    with pytest.raises(FileExistsError):
        at07.create_probe(configuration(), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="same-reference", api_key="fake-key", root=root)
    assert len(calls) == 1


def test_changed_probe_source_never_reaches_sdk(tmp_path):
    root = prepared(tmp_path)
    (root / "at07-probe.py").write_text("print('substituted candidate')")
    with pytest.raises(ValueError, match="fixed_probe_source_changed"):
        at07.create_probe(configuration(), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="fixture", api_key="fake", root=root)
    assert not (root / "create-requested.json").exists()


def test_create_disconnect_is_durable_unknown_and_cannot_repeat(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    create = Mock(side_effect=TimeoutError("transport disconnected"))
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    with pytest.raises(TimeoutError):
        at07.create_probe(configuration(), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="fixture", api_key="fake", root=root)
    result = at07.At07Result.model_validate_json((root / "result.json").read_bytes())
    assert result.remote_effect == result.cleanup_state == "unknown"
    assert result.sandbox_id is None
    with pytest.raises(FileExistsError):
        at07.create_probe(configuration(), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="fixture", api_key="fake", root=root)
    create.assert_called_once()


def test_cleanup_reuses_original_session_and_rejects_other_ids(tmp_path):
    sandbox = Mock(id="owned-id")
    session = OpenSandboxSession(sandbox, owned=True)
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance="live", sandbox_id=session.id)
    result = at07.finish(session, result, tmp_path)
    sandbox.kill.assert_called_once_with()
    sandbox.close.assert_called_once_with()
    assert result.cleanup_state == "destroyed" and at07.review(result)["cleanup"] == "unknown"
    other = Mock(id="someone-else", owned=True)
    with pytest.raises(PermissionError, match="identity_mismatch"):
        at07.finish(other, result, tmp_path)
    other.destroy.assert_not_called()
    session.owned = False
    with pytest.raises(PermissionError):
        at07.finish(session, result, tmp_path)


def complete_observations():
    host = dict.fromkeys(("effective_configuration_matches", "expiry_observed", "canary_unchanged",
        "canary_positive_control", "fake_credential_control", "no_host_mounts_or_control",
        "target_positive_before_and_after", "no_denied_target_hits", "effective_nft_default_deny",
        "target_dns_positive", "egress_domain_denial_observed", "timeout_marker_absent",
        "cleanup_observed", "unrelated_resources_unchanged"), True)
    data = {
        "host": host,
        "filesystem": {"data": {"access": [{"read": 2, "write": 2}] * 3, "control_sockets": [],
            "fake_credential_visible": False, "privilege": {"NoNewPrivs": "1", "CapEff": "0" * 16,
            "CapBnd": "0" * 16, "raw_socket": 1, "unshare": -1, "unshare_errno": 1}}},
        "export": {"small": True, "large": "artifact_size_limit", **dict.fromkeys(("absolute", "traversal", "symlink"), "artifact_path_escape")},
        "network": {"data": {"direct_ipv4": "timeout", "domain": {"id": 1707, "rcode": 3, "answers": 0},
            "ipv6_disabled": dict.fromkeys(("all", "default", "lo"), "1"), "ipv6_bind": 99}},
        "timeout": {"error": {"name": "CommandTimeout"}, "status": {"running": False}, "elapsed": 30},
    }
    for name, file, value, counter in (("cpu", "cpu.max", "100000 100000", "nr_throttled"),
            ("memory", "memory.max", "536870912", "max"), ("pids", "pids.max", "128", "max")):
        data[name] = {"data": {"limits": {file: value}, "before": {counter: 0}, "after": {counter: 1}, "fork_errno": 11}}
    return data


def test_complete_diagnostic_positive_still_cannot_mint_trust():
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance="live", sandbox_id="inert",
        observations=complete_observations(), remote_effect="known", cleanup_state="destroyed")
    checks = at07.review(result)
    assert checks["export"] == "unsupported"
    assert all(status == "passed" for name, status in checks.items() if name != "export")
    record = at07.unverified_record(result, "static-inert-data")
    assert record.verified is False and record.passed is False
    assert not record.declared.process_limit
    assert not record.declared.export_bounded
    forged = IsolationReport(backend="opensandbox", declared=record.declared, verified=True,
        probe="passed", proof_ref=record.probe_id, configuration=record.configuration)
    assert TrustedProbeRegistry((record,)).is_verified(forged) is False


@pytest.mark.parametrize("provenance", ["mock", "replay"])
def test_mock_and_replay_complete_data_are_not_live_evidence(provenance):
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance=provenance,
        sandbox_id="inert", observations=complete_observations(), remote_effect="known", cleanup_state="destroyed")
    assert set(at07.review(result).values()) == {"not_run"}
    assert not at07.unverified_record(result, "fixture").verified


def test_missing_unknown_unsupported_and_failed_are_distinct():
    data = complete_observations()
    del data["host"]["egress_domain_denial_observed"]
    data["host"]["unsupported"] = ["ipv6"]
    data["cpu"]["data"]["after"]["nr_throttled"] = 0
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance="live", sandbox_id="inert",
        observations=data, remote_effect="unknown", cleanup_state="destroyed")
    checks = at07.review(result)
    assert checks["domain"] == checks["cleanup"] == "unknown"
    assert checks["ipv6"] == "unsupported" and checks["cpu"] == "failed"


def test_operator_never_mutates_docker_or_prints_secret_fields():
    for args in (("rm", "owned"), ("start", "owned"), ("update", "owned"), ("compose", "up"), ("pull", "image")):
        with pytest.raises(PermissionError, match="docker_read_only"):
            at07_live.docker_read(*args)
    assert ".Config.Env" not in at07_live.INSPECT
    assert "{{json .Config.Labels}}" not in at07_live.INSPECT
    assert "egress-auth" not in at07_live.INSPECT


def test_operator_disconnected_create_is_not_replayed_or_overwritten(tmp_path, monkeypatch):
    # Inert future-capability fixture solely exercises the existing lifecycle.
    # No real supported atomic export or live proof is asserted by this test.
    monkeypatch.setattr(at07_live, "ATOMIC_EXPORT_SCOPE_SUPPORTED", True)
    root = prepared(tmp_path)
    canary = tmp_path / "canary"
    canary.mkdir()
    (canary / "credentials").write_bytes(b"AT07-SYNTHETIC-NOT-A-SECRET\n")
    key = tmp_path / "fake-service-key"
    key.write_text("fake-fixture-only")
    def inspecting(name):
        return {"id": configuration().instance_id, "image": at07.SERVER_IMAGE if name.endswith("server") else PYTHON_IMAGE,
                "owner": "r1-at07", "state": "running", "ip": "172.17.0.2"}
    monkeypatch.setattr(at07_live, "inspect", inspecting)
    monkeypatch.setattr(at07_live, "docker_read", lambda *args: CONFIG.read_text())
    monkeypatch.setattr(at07_live, "inventory", lambda: {"containers": ["unrelated"], "volumes": ["old-volume"], "networks": ["bridge"]})
    monkeypatch.setattr(at07_live, "target_control", lambda: {"dns_positive": True, "canary_exists": True,
        "fake_credential_present": True, "denied_tcp_hits": 0, "dns_queries": 0})
    create = Mock(side_effect=TimeoutError("offline disconnect fixture"))
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    result = at07_live.execute(root=root, authorization_ref="fixture-not-permission", key_file=key,
                               canary_directory=canary, accept_infrastructure_limits=True)
    assert result.remote_effect == result.cleanup_state == "unknown"
    assert "create_unknown_TimeoutError" in result.reasons
    first = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    with pytest.raises(FileExistsError, match="not_replayable"):
        at07_live.execute(root=root, authorization_ref="fixture-not-permission", key_file=key,
                         canary_directory=canary, accept_infrastructure_limits=True)
    assert first == {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    create.assert_called_once()


def test_current_operator_stops_before_any_docker_or_key_read(tmp_path):
    with pytest.raises(ValueError, match="atomic_export_scope_unsupported"):
        at07_live.execute(root=tmp_path / "missing", authorization_ref="fixture-not-permission",
                         key_file=tmp_path / "must-not-read", canary_directory=tmp_path / "missing-canary",
                         accept_infrastructure_limits=True)
    assert not list(tmp_path.iterdir())


def test_actual_violations_still_fail_when_host_corroboration_is_missing():
    data = complete_observations()
    data["host"] = {}
    data["network"]["data"]["direct_ipv4"] = "connected"
    data["filesystem"]["data"]["access"][0]["write"] = "accessible"
    data["filesystem"]["data"]["fake_credential_visible"] = True
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance="live",
                            sandbox_id="inert", observations=data)
    checks = at07.review(result)
    assert checks["ipv4"] == checks["host_files"] == checks["credentials"] == "failed"
    assert checks["domain"] == "unknown"


def test_effective_config_requires_actual_owned_container_and_not_sdk_parameters():
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance="live", sandbox_id="sid")
    main = {"probe": "fixture", "image": configuration().environment.image, "privileged": False, "cpu": 1000000000,
        "memory": 536870912, "pids": 128, "caps_drop": ["ALL"], "caps_add": [], "security": ["no-new-privileges=true"],
        "network": "container:sidecar", "mounts": [{"Type": "volume", "Name": "opensandbox-runtime-sid", "Destination": "/opt/opensandbox"}]}
    sidecar = {"id": "sidecar", "sidecar_for": "sid", "image": at07.EGRESS_IMAGE, "privileged": False, "network": "bridge"}
    assert at07_live.effective(main, sidecar, result)
    for changed in ({**main, "pids": 0}, {**main, "privileged": True}, {**main, "caps_add": ["SYS_ADMIN"]},
                    {**main, "mounts": [{"Type": "bind", "Source": "/host", "Destination": "/host"}]},
                    {**main, "probe": "another-probe"}):
        assert not at07_live.effective(changed, sidecar, result)
    assert not at07_live.effective(main, {**sidecar, "sidecar_for": "unrelated"}, result)
