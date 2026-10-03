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
from orchestration.experiments.generated import ApprovedEnvironment, BackendProfile, DockerExportConfiguration, IsolationConfiguration, IsolationReport, effective_environment
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
    monkeypatch.setattr(at07, "FrozenDockerExport", denied)
    monkeypatch.setattr(at07_live, "FrozenDockerExport", denied)


def configuration(*, frozen=False):
    return IsolationConfiguration(endpoint="http://127.0.0.1:8099", instance_id="1" * 64,
        runtime_profile="git:" + "a" * 40 + ":deploy/opensandbox/at07.config.toml",
        environment=effective_environment(ApprovedEnvironment(image=PYTHON_IMAGE, dependency_lock_sha256="0" * 64)),
        resources=BackendProfile(process_limit=128), network_deny=True, server_process_limit=128,
        docker_export=(DockerExportConfiguration(endpoint="npipe:////./pipe/dockerDesktopLinuxEngine",
            daemon_id="inert-daemon-1", engine_version="29.5.3") if frozen else None))


def prepared(tmp_path, *, frozen=False):
    return at07.prepare(configuration(frozen=frozen), CONFIG.read_bytes(), probe_id="fixture", target_ipv4="172.17.0.2", archive_root=tmp_path)


@pytest.fixture
def inert_control(monkeypatch):
    control = SimpleNamespace(preflight=Mock(), close=Mock(), _json=Mock(return_value={"ApiVersion": "1.52"}))
    monkeypatch.setattr(at07, "FrozenDockerExport", lambda config: control)
    monkeypatch.setattr(at07_live, "FrozenDockerExport", lambda config: control)
    return control


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


def test_sdk_probe_create_is_one_official_bounded_deny_request(tmp_path, monkeypatch, inert_control):
    root = prepared(tmp_path, frozen=True)
    calls = []
    def capture(image, **options):
        calls.append((image, options))
        return SimpleNamespace(id="inert-sdk-id")
    monkeypatch.setattr(at07.SandboxSync, "create", capture)
    session, result = at07.create_probe(configuration(frozen=True), CONFIG.read_bytes(), probe_id="fixture",
        authorization_ref="inert-test-reference-not-authorization", api_key="fake-key", root=root)
    assert session.id == result.sandbox_id == "inert-sdk-id" and len(calls) == 1
    inert_control.preflight.assert_called_once()
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
        at07.create_probe(configuration(frozen=True), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="same-reference", api_key="fake-key", root=root)
    assert len(calls) == 1


def test_changed_probe_source_never_reaches_sdk(tmp_path):
    root = prepared(tmp_path, frozen=True)
    (root / "at07-probe.py").write_text("print('substituted candidate')")
    with pytest.raises(ValueError, match="fixed_probe_source_changed"):
        at07.create_probe(configuration(frozen=True), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="fixture", api_key="fake", root=root)
    assert not (root / "create-requested.json").exists()


def test_create_disconnect_is_durable_unknown_and_cannot_repeat(tmp_path, monkeypatch, inert_control):
    root = prepared(tmp_path, frozen=True)
    create = Mock(side_effect=TimeoutError("transport disconnected"))
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    with pytest.raises(TimeoutError):
        at07.create_probe(configuration(frozen=True), CONFIG.read_bytes(), probe_id="fixture",
            authorization_ref="fixture", api_key="fake", root=root)
    result = at07.At07Result.model_validate_json((root / "result.json").read_bytes())
    assert result.remote_effect == result.cleanup_state == "unknown"
    assert result.sandbox_id is None
    with pytest.raises(FileExistsError):
        at07.create_probe(configuration(frozen=True), CONFIG.read_bytes(), probe_id="fixture",
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


def test_operator_disconnected_create_is_not_replayed_or_overwritten(tmp_path, monkeypatch, inert_control):
    # Inert future-capability fixture solely exercises the existing lifecycle.
    # No real supported atomic export or live proof is asserted by this test.
    monkeypatch.setattr(at07_live, "ATOMIC_EXPORT_SCOPE_SUPPORTED", True)
    root = prepared(tmp_path, frozen=True)
    canary = tmp_path / "canary"
    canary.mkdir()
    (canary / "credentials").write_bytes(b"AT07-SYNTHETIC-NOT-A-SECRET\n")
    key = tmp_path / "fake-service-key"
    key.write_text("fake-fixture-only")
    calls = []
    def process(argv, **options):
        calls.append((argv, options))
        args = argv[5:]
        if args[0] == "inspect":
            output = json.dumps({"id": configuration().instance_id,
                "image": at07.SERVER_IMAGE if args[-1].endswith("server") else PYTHON_IMAGE,
                "owner": "r1-at07", "state": "running", "ip": "172.17.0.2"})
        elif args[0] == "exec":
            output = CONFIG.read_text()
        else:
            output = {"ps": "unrelated", "volume": "old-volume", "network": "bridge"}[args[0]]
        return SimpleNamespace(returncode=0, stdout=output, stderr="")
    monkeypatch.setattr(subprocess, "run", process)
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
    assert len(calls) == 9  # Both inventories, two inspects, fixed server-config exec.
    for argv, options in calls:
        assert argv[:5] == ["docker", "--host", configuration(frozen=True).docker_export.endpoint,
                            "--config", str(root / ".at07-docker-cli")]
        assert options["shell"] is False
        assert not any(k.upper().startswith("DOCKER_") or "PROXY" in k.upper() for k in options["env"])
    assert not (root / ".at07-docker-cli").exists()


def test_docker_read_without_binding_and_nonempty_config_never_spawns(tmp_path, monkeypatch):
    process = Mock(side_effect=AssertionError("must not spawn"))
    monkeypatch.setattr(subprocess, "run", process)
    private = tmp_path / ".at07-docker-cli"
    private.mkdir()
    secret = private / "config.json"
    secret.write_text('{"auths":{"foreign":"fake-secret"}}')
    with pytest.raises(ValueError, match="configuration_required"):
        at07_live.docker_read("ps", "-aq", "--no-trunc", private_config=private)
    with pytest.raises(ValueError, match="empty_docker_config_required"):
        at07_live.docker_read("ps", "-aq", "--no-trunc",
            configuration=configuration(frozen=True).docker_export, private_config=private)
    assert secret.read_text() == '{"auths":{"foreign":"fake-secret"}}'
    process.assert_not_called()


def test_private_docker_config_does_not_overwrite_or_remove_unknown_files(tmp_path):
    private = tmp_path / ".at07-docker-cli"
    private.mkdir()
    original = private / "original"
    original.write_text("retain")
    with pytest.raises(FileExistsError):
        with at07_live._private_docker_config(tmp_path):
            pytest.fail("must not enter an existing directory")
    assert original.read_text() == "retain"
    root = tmp_path / "new-root"
    root.mkdir()
    with pytest.raises(OSError):
        with at07_live._private_docker_config(root) as owned:
            (owned / "unexpected").write_text("retain-new")
    assert (root / ".at07-docker-cli/unexpected").read_text() == "retain-new"


@pytest.mark.parametrize("field,value", [("instance_id", "UNBOUND-NOT-RUN"),
    ("runtime_profile", "unverified"), ("endpoint", "http://foreign:8099"), ("server_process_limit", 16)])
def test_invalid_complete_operator_configuration_stops_before_transport(tmp_path, monkeypatch, field, value):
    root = prepared(tmp_path, frozen=True)
    altered = configuration(frozen=True).model_copy(update={field: value})
    (root / "configuration.json").write_text(altered.model_dump_json())
    transport = Mock(side_effect=AssertionError("must not construct transport"))
    process = Mock(side_effect=AssertionError("must not spawn"))
    monkeypatch.setattr(at07_live, "FrozenDockerExport", transport)
    monkeypatch.setattr(subprocess, "run", process)
    with pytest.raises(ValueError):
        at07_live.execute(root=root, authorization_ref="fixture", key_file=tmp_path / "must-not-read",
            canary_directory=tmp_path / "missing", accept_infrastructure_limits=True)
    transport.assert_not_called()
    process.assert_not_called()
    assert not (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("fake-secret-argv", 10),
                                    OSError("fake-secret-path")])
def test_docker_process_errors_remain_secret_free(tmp_path, monkeypatch, failure):
    private = tmp_path / ".at07-docker-cli"
    private.mkdir()
    monkeypatch.setattr(subprocess, "run", Mock(side_effect=failure))
    with pytest.raises(RuntimeError, match="^docker_read_failed$") as caught:
        at07_live.docker_read("ps", "-aq", "--no-trunc",
            configuration=configuration(frozen=True).docker_export, private_config=private)
    assert caught.value.__suppress_context__ is True


def test_unconfigured_operator_stops_before_any_docker_or_key_read(tmp_path):
    root = prepared(tmp_path)
    first = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    with pytest.raises(ValueError, match="frozen_export_configuration_required"):
        at07_live.execute(root=root, authorization_ref="fixture-not-permission",
                         key_file=tmp_path / "must-not-read", canary_directory=tmp_path / "missing-canary",
                         accept_infrastructure_limits=True)
    assert first == {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}


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


@pytest.mark.parametrize("endpoint", ["npipe:////./pipe/dockerDesktopLinuxEngine", "unix:///var/run/docker.sock"])
def test_docker_reads_bind_explicit_endpoint_and_ignore_poison_environment(tmp_path, monkeypatch, endpoint):
    private = tmp_path / ".at07-docker-cli"
    private.mkdir()
    config = configuration(frozen=True).docker_export.model_copy(update={"endpoint": endpoint})
    poison = {"PATH": "trusted-tool-path", "SystemRoot": "C:/Windows", "HOME": "secret-home",
        "USERPROFILE": "secret-profile", "DOCKER_CONTEXT": "foreign", "docker_host": "tcp://foreign:2375",
        "DoCkEr_CoNfIg": "secret-config", "DOCKER_TLS_VERIFY": "1", "DOCKER_CERT_PATH": "secret-certs",
        "DOCKER_API_VERSION": "1.20", "DOCKER_CUSTOM_HEADERS": "Authorization=secret",
        "http_proxy": "secret-proxy", "HTTPS_PROXY": "secret-proxy", "ALL_PROXY": "secret-proxy",
        "NO_PROXY": "foreign", "OPENSANDBOX_SERVER_API_KEY": "secret-service-key"}
    monkeypatch.setattr(at07_live.os, "environ", poison)
    calls = []
    def capture(argv, **kwargs):
        calls.append((argv, kwargs))
        assert private.is_dir() and list(private.iterdir()) == []
        return SimpleNamespace(returncode=0, stdout="[]", stderr="")
    monkeypatch.setattr(subprocess, "run", capture)
    commands = [("inspect", "--format", at07_live.INSPECT, "1" * 64), ("ps", "-aq", "--no-trunc"),
        ("volume", "ls", "-q"), ("network", "ls", "-q", "--no-trunc"),
        ("exec", "1" * 64, "cat", "/etc/opensandbox/config.toml"),
        ("exec", "2" * 64, "nft", "-j", "list", "ruleset"), ("logs", "--tail", "100", "2" * 64)]
    for args in commands:
        at07_live.docker_read(*args, configuration=config, private_config=private)
    assert len(calls) == len(commands)
    for (argv, options), command in zip(calls, commands, strict=True):
        assert argv == ["docker", "--host", endpoint, "--config", str(private), *command]
        assert options["shell"] is False and options["timeout"] == 10
        assert set(options["env"]) == {"PATH", "SYSTEMROOT"}
        assert options["env"] == {"PATH": "trusted-tool-path", "SYSTEMROOT": "C:/Windows"}
        assert options["cwd"] == private
    assert poison["DOCKER_CONTEXT"] == "foreign" and poison["HOME"] == "secret-home"


@pytest.mark.parametrize("args", [
    ("inspect", "--host", "tcp://foreign", "1" * 64), ("ps", "--context=foreign"),
    ("ps", "-Htcp://foreign"), ("logs", "--config", "secret-config", "1" * 64),
    ("ps", "--tlsverify"), ("exec", "1" * 64, "sh", "-c", "true"), ("volume", "rm", "foreign"),
])
def test_docker_read_rejects_routing_overrides_and_mutation_before_process(tmp_path, monkeypatch, args):
    process = Mock(side_effect=AssertionError("must not spawn"))
    monkeypatch.setattr(subprocess, "run", process)
    with pytest.raises(PermissionError, match="docker_read_only"):
        at07_live.docker_read(*args, configuration=configuration(frozen=True).docker_export,
                              private_config=tmp_path / ".at07-docker-cli")
    process.assert_not_called()


@pytest.mark.parametrize("field,value", [("endpoint", "tcp://foreign:2375"), ("api_version", "1.20"),
    ("engine_version", "unknown"), ("daemon_id", ""), ("request_timeout_seconds", 45)])
def test_docker_read_revalidates_even_bypassed_model_before_process(tmp_path, monkeypatch, field, value):
    process = Mock(side_effect=AssertionError("must not spawn"))
    monkeypatch.setattr(subprocess, "run", process)
    config = configuration(frozen=True).docker_export.model_copy(update={field: value})
    with pytest.raises(ValueError):
        at07_live.docker_read("ps", "-aq", "--no-trunc", configuration=config,
                              private_config=tmp_path / ".at07-docker-cli")
    process.assert_not_called()


@pytest.mark.parametrize("change", [{"Version": "other"}, {"ApiVersion": "1.20"},
                                    {"ID": "foreign-daemon"}, {"Os": "windows"}])
def test_operator_engine_mismatch_stops_before_cli_key_or_create(tmp_path, monkeypatch, change):
    from orchestration.experiments import frozen_export
    root = prepared(tmp_path, frozen=True)
    transport = Mock()
    monkeypatch.setattr(frozen_export, "_transport", lambda endpoint: (transport, "http+docker://inert"))
    def original_json(control, path):
        if path == "/version":
            return {"Version": "29.5.3", "Os": "linux", "ApiVersion": "1.52", **change}
        if path == "/info":
            return {"ID": "inert-daemon-1", "OSType": "linux", **change}
        return {"Id": "1" * 64, "State": {"Running": True}, "Config": {"Image": at07.SERVER_IMAGE},
            "NetworkSettings": {"Ports": {"8090/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8099"}]}}}
    monkeypatch.setattr(frozen_export.FrozenDockerExport, "_json", original_json)
    monkeypatch.setattr(at07_live, "FrozenDockerExport", frozen_export.FrozenDockerExport)
    process = Mock(side_effect=AssertionError("must not spawn"))
    create = Mock(side_effect=AssertionError("must not create"))
    monkeypatch.setattr(subprocess, "run", process)
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    with pytest.raises(PermissionError, match="daemon_mismatch|api_mismatch"):
        at07_live.execute(root=root, authorization_ref="fixture-not-permission", key_file=tmp_path / "must-not-read",
            canary_directory=tmp_path / "missing", accept_infrastructure_limits=True)
    process.assert_not_called()
    create.assert_not_called()
    transport.close.assert_called_once()
    assert not (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()


@pytest.mark.parametrize("bound_api,actual_api", [("1.52", "1.54"), ("1.54", "1.52")])
def test_supported_but_different_engine_api_stops_before_cli_key_or_sdk(tmp_path, monkeypatch, bound_api, actual_api):
    config = configuration(frozen=True)
    config = config.model_copy(update={"docker_export": DockerExportConfiguration(
        **{**config.docker_export.model_dump(), "api_version": bound_api})})
    root = at07.prepare(config, CONFIG.read_bytes(), probe_id="api-mismatch",
        target_ipv4="172.17.0.2", archive_root=tmp_path)
    control = SimpleNamespace(preflight=Mock(), close=Mock(), _json=Mock(return_value={"ApiVersion": actual_api}))
    monkeypatch.setattr(at07_live, "FrozenDockerExport", lambda value: control)
    process, create = Mock(), Mock()
    monkeypatch.setattr(subprocess, "run", process)
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    with pytest.raises(PermissionError, match="^docker_export_api_mismatch$"):
        at07_live.execute(root=root, authorization_ref="inert-reference", key_file=tmp_path / "must-not-read",
            canary_directory=tmp_path / "missing", accept_infrastructure_limits=True)
    process.assert_not_called()
    create.assert_not_called()
    control.preflight.assert_called_once()
    control.close.assert_called_once()
    assert not (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()


def test_bound_api_154_operator_gate_preserves_configuration(tmp_path, monkeypatch):
    config = configuration(frozen=True)
    config = config.model_copy(update={"docker_export": DockerExportConfiguration(
        **{**config.docker_export.model_dump(), "api_version": "1.54"})})
    root = at07.prepare(config, CONFIG.read_bytes(), probe_id="api-154",
        target_ipv4="172.17.0.2", archive_root=tmp_path)
    control = SimpleNamespace(preflight=Mock(), close=Mock(), _json=Mock(return_value={"ApiVersion": "1.54"}))
    captured = Mock(return_value=at07.At07Result(probe_id="api-154", configuration=config, provenance="mock"))
    monkeypatch.setattr(at07_live, "FrozenDockerExport", lambda value: control)
    monkeypatch.setattr(at07_live, "_execute", captured)
    result = at07_live.execute(root=root, authorization_ref="inert-reference", key_file=tmp_path / "must-not-read",
        canary_directory=tmp_path / "missing", accept_infrastructure_limits=True)
    assert result.configuration == captured.call_args.kwargs["config"] == config
    captured.assert_called_once()
    control.preflight.assert_called_once()
    control._json.assert_called_once_with("/version")
    control.close.assert_called_once()
    assert not (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()
