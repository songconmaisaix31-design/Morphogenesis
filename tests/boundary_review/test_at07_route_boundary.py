"""Independent AT07 observer boundaries; contract_local intercepted I/O only.

Run with an exact noneditable install from outside the source checkout. Synthetic
fixtures are neither Engine evidence nor permission to execute a real probe.
"""

import io
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from orchestration.experiments import at07, at07_live as live, frozen_export
from orchestration.experiments.backend import OpenSandboxSession, UnsupportedCapability
from orchestration.experiments.case import PYTHON_IMAGE
from orchestration.experiments.generated import (
    ApprovedEnvironment, BackendProfile, DockerExportConfiguration,
    IsolationConfiguration, effective_environment,
)
from local_assets.models import AssetSafetyError
from local_assets import paths as asset_paths

SERVER_ID, TARGET_ID, MAIN_ID, SIDECAR_ID = (c * 64 for c in "1234")
ENDPOINTS = ("unix:///var/run/docker.sock", "npipe:////./pipe/dockerDesktopLinuxEngine")
CONFIG_FILE = Path(os.environ.get("Q_AT07_SERVER_CONFIG", str(
    Path(__file__).resolve().parents[2] / "deploy/opensandbox/at07.config.toml")))


def configuration(endpoint=ENDPOINTS[0]):
    return IsolationConfiguration(
        endpoint="http://127.0.0.1:8099", instance_id=SERVER_ID,
        runtime_profile="git:" + "a" * 40 + ":deploy/opensandbox/at07.config.toml",
        environment=effective_environment(ApprovedEnvironment(
            image=PYTHON_IMAGE, dependency_lock_sha256="0" * 64)),
        resources=BackendProfile(process_limit=128), network_deny=True,
        server_process_limit=128,
        docker_export=DockerExportConfiguration(endpoint=endpoint,
            daemon_id="q-synthetic-daemon", engine_version="29.5.3"))


def prepared(tmp_path, config=None):
    return at07.prepare(config or configuration(), CONFIG_FILE.read_bytes(),
        probe_id="q-route", target_ipv4="172.17.0.2", archive_root=tmp_path)


def execute(root, key):
    return live.execute(root=root, authorization_ref="Q-MOCK-NOT-AUTHORIZATION",
        key_file=key, canary_directory=root / "canary",
        accept_infrastructure_limits=True)


def capture_cli(monkeypatch, output=""):
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def spy_key(monkeypatch, key):
    reads = []
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path == key:
            reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    return reads


class SyntheticEngine:
    """Mock bytes at the original transport seam; original preflight runs."""

    def __init__(self, config, changed=None):
        export = config.docker_export
        self.version = {"Version": export.engine_version, "ApiVersion": export.api_version, "Os": "linux"}
        self.info = {"ID": export.daemon_id, "OSType": "linux"}
        self.server = {"Id": SERVER_ID, "Config": {"Image": at07.SERVER_IMAGE},
            "State": {"Running": True}, "NetworkSettings": {"Ports": {
                "8090/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8099"}]}}}
        if changed:
            target, key, value = changed
            getattr(self, target)[key] = value
        self.calls = []
        self.closed = 0

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        value = self.version if url.endswith("/version") else (
            self.info if url.endswith("/info") else self.server)
        body = io.BytesIO(json.dumps(value).encode())
        raw = SimpleNamespace(read1=lambda n, **ignored: body.read(n))
        return SimpleNamespace(status_code=200, raw=raw, close=lambda: None)

    def close(self):
        self.closed += 1


def bind_transport(monkeypatch, config, changed=None):
    engines, endpoints = [], []

    def transport(endpoint):
        endpoints.append(endpoint)
        engine = SyntheticEngine(config, changed)
        engines.append(engine)
        return engine, "http+docker://q-contract-local"

    monkeypatch.setattr(frozen_export, "_transport", transport)
    return engines, endpoints


@pytest.fixture(autouse=True)
def deny_external_io(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("Q contract_local forbids process/network/SDK I/O")

    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket.socket, "sendto", denied)
    monkeypatch.setattr(at07.SandboxSync, "create", denied)
    monkeypatch.setattr(frozen_export, "_transport", denied)


def test_unbound_observation_cannot_reach_cli(monkeypatch):
    """Omitting the trusted binding must not use the operator's Docker context."""
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", capture)
    with pytest.raises((PermissionError, ValueError, TypeError)):
        live.docker_read("ps", "-aq", "--no-trunc")
    assert calls == [], "unbound observation reached CLI before rejection"


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_poisoned_operator_environment_cannot_change_cli_route(tmp_path, monkeypatch, endpoint):
    """Every Docker/auth/proxy/API source is absent from the spawned environment."""
    poison = {key: "Q-POISON-" + key for key in (
        "DOCKER_CONTEXT", "DOCKER_HOST", "DOCKER_CONFIG", "DOCKER_CERT_PATH",
        "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_API_VERSION", "DOCKER_AUTH_CONFIG",
        "DOCKER_CUSTOM_HEADERS", "DOCKER_CLI_PLUGIN_EXTRA_DIRS", "HTTP_PROXY",
        "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY", "HOME", "USERPROFILE", "XDG_CONFIG_HOME",
        "docker_context", "Docker_Host", "docker_config", "https_proxy")}
    monkeypatch.setattr(live.os, "environ", {**poison, "Path": "Q-CLI-PATH",
        "SystemRoot": "Q-SYSTEM", "windir": "Q-WINDOWS"})
    directory = tmp_path / ".at07-docker-cli"
    directory.mkdir()
    calls = capture_cli(monkeypatch)
    live.docker_read("ps", "-aq", "--no-trunc",
        configuration=configuration(endpoint).docker_export, private_config=directory)
    argv, options = calls[0]
    assert argv == ["docker", "--host", endpoint, "--config", str(directory), "ps", "-aq", "--no-trunc"]
    assert options["env"] == {"PATH": "Q-CLI-PATH", "SYSTEMROOT": "Q-SYSTEM", "WINDIR": "Q-WINDOWS"}
    assert options["shell"] is False and options["timeout"] == 10
    assert options["cwd"] == directory and options["check"] is False
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("argv", [
    ("--host", "unix:///wrong", "ps", "-aq", "--no-trunc"),
    ("ps", "-aq", "--no-trunc", "--context", "wrong"),
    ("ps", "-aq", "--no-trunc", "--config=other"),
    ("ps", "-aq", "--no-trunc", "--tlsverify"),
    ("ps", "-aq", "--no-trunc", "--tlscert=other"),
    ("ps", "-aq", "--no-trunc", "--filter", "label=opensandbox.io/egress-sidecar-for=ok --host=other"),
    ("inspect", "--format", "{{json .Config.Env}}", SERVER_ID),
    ("inspect", "--format", live.INSPECT, "--host=other"),
    ("logs", "--tail", "100", SIDECAR_ID, "--follow"),
    ("exec", SERVER_ID, "sh", "-c", "cat /etc/opensandbox/config.toml"),
    ("exec", "morph-r1-at07-server", "cat", "/etc/opensandbox/config.toml"),
    ("exec", SERVER_ID, "nft", "-j", "list", "ruleset", "--host=other"),
    ("exec", SERVER_ID, "cat", "/etc/opensandbox/config.toml", "/secret"),
    ("rm", MAIN_ID), ("kill", MAIN_ID), ("run", "python:latest"),
    ("volume", "rm", "other"), ("network", "rm", "other"), ("system", "prune"),
])
def test_route_option_and_mutation_bypasses_refused_before_cli(tmp_path, monkeypatch, argv):
    directory = tmp_path / ".at07-docker-cli"
    directory.mkdir()
    calls = capture_cli(monkeypatch)
    with pytest.raises(PermissionError, match="docker_read_only"):
        live.docker_read(*argv, configuration=configuration().docker_export, private_config=directory)
    assert calls == []


@pytest.mark.parametrize("change", [
    ("docker_export", None), ("missing", "endpoint"), ("missing", "daemon_id"),
    ("missing", "engine_version"), ("endpoint", "tcp://wrong:2375"),
    ("api_version", "1.53"), ("engine_version", "29.5.4"),
    ("request_timeout_seconds", 11), ("extra", "host"),
    ("conflicting_service", "http://127.0.0.1:9999"),
])
def test_incomplete_invalid_or_conflicting_config_never_reads_key_or_creates(tmp_path, monkeypatch, change):
    root = prepared(tmp_path)
    doc = json.loads((root / "configuration.json").read_bytes())
    field, value = change
    if field == "docker_export":
        doc[field] = value
    elif field == "missing":
        del doc["docker_export"][value]
    elif field == "extra":
        doc["docker_export"][value] = "unix:///wrong"
    elif field == "conflicting_service":
        doc["endpoint"] = value
    else:
        doc["docker_export"][field] = value
    (root / "configuration.json").write_text(json.dumps(doc))
    key = root / "key-never-read"
    reads = spy_key(monkeypatch, key)
    calls = capture_cli(monkeypatch)
    create = Mock(side_effect=AssertionError("configuration must reject before SDK"))
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    with pytest.raises((ValueError, UnsupportedCapability)):
        execute(root, key)
    assert calls == reads == [] and create.call_count == 0
    assert not (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()


@pytest.mark.parametrize("changed", [
    ("info", "ID", "wrong-daemon"), ("version", "Version", "29.5.4"),
    ("version", "ApiVersion", "1.53"), ("version", "ApiVersion", None),
    ("version", "Os", "windows"), ("info", "OSType", "windows"),
])
def test_original_preflight_rejects_daemon_version_api_before_key_and_cli(tmp_path, monkeypatch, changed):
    config = configuration()
    root = prepared(tmp_path, config)
    engines, endpoints = bind_transport(monkeypatch, config, changed)
    key = root / "key-never-read"
    reads = spy_key(monkeypatch, key)
    calls = capture_cli(monkeypatch)
    create = Mock(side_effect=AssertionError("preflight must reject before SDK"))
    monkeypatch.setattr(at07.SandboxSync, "create", create)
    with pytest.raises(PermissionError, match="docker_export_(daemon|api)_mismatch"):
        execute(root, key)
    assert endpoints == [config.docker_export.endpoint]
    assert calls == reads == [] and create.call_count == 0
    assert engines[0].closed == 1
    assert all(method == "GET" and "/v1.52/" in url for method, url, _ in engines[0].calls)
    assert not (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()


@pytest.mark.parametrize("state", ["absent", "nonempty", "unknown", "symlink", "junction"])
def test_untrusted_private_config_directory_cannot_reach_cli(tmp_path, monkeypatch, state):
    directory = tmp_path / ".at07-docker-cli"
    if state != "absent":
        directory.mkdir()
    sentinel = directory / "config.json"
    if state == "nonempty":
        sentinel.write_bytes(b"Q-UNOWNED-AUTH-SENTINEL")
    if state in {"unknown", "symlink", "junction"}:
        original = Path.lstat
        if state == "junction":
            monkeypatch.setattr(asset_paths, "sys", SimpleNamespace(platform="win32"))

        def lstat(path, *args, **kwargs):
            if path == directory:
                if state == "unknown":
                    raise PermissionError("Q unknown path ownership")
                return SimpleNamespace(st_mode=stat.S_IFDIR if state == "junction" else stat.S_IFLNK,
                    st_reparse_tag=0xA0000003, st_nlink=1)
            metadata = original(path, *args, **kwargs)
            if state == "junction":
                return SimpleNamespace(st_mode=metadata.st_mode, st_nlink=metadata.st_nlink, st_reparse_tag=0)
            return metadata

        monkeypatch.setattr(Path, "lstat", lstat)
    calls = capture_cli(monkeypatch)
    with pytest.raises((ValueError, PermissionError, AssetSafetyError)):
        live.docker_read("ps", "-aq", "--no-trunc", configuration=configuration().docker_export,
            private_config=directory)
    assert calls == []
    if state == "nonempty":
        assert sentinel.read_bytes() == b"Q-UNOWNED-AUTH-SENTINEL"


def test_case_conflicting_required_process_environment_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(live.os, "environ", {"PATH": "one", "Path": "two"})
    directory = tmp_path / ".at07-docker-cli"
    directory.mkdir()
    calls = capture_cli(monkeypatch)
    with pytest.raises(ValueError, match="conflicting_docker_process_environment"):
        live.docker_read("ps", "-aq", "--no-trunc", configuration=configuration().docker_export,
            private_config=directory)
    assert calls == []


def test_public_execute_does_not_adopt_a_preexisting_config_directory(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    directory = root / ".at07-docker-cli"
    directory.mkdir()
    sentinel = directory / "config.json"
    sentinel.write_bytes(b"Q-UNKNOWN-OWNER")
    key = root / "unread-key"
    reads = spy_key(monkeypatch, key)
    calls = capture_cli(monkeypatch)
    with pytest.raises(FileExistsError):
        execute(root, key)
    assert sentinel.read_bytes() == b"Q-UNKNOWN-OWNER"
    assert calls == reads == [] and not (root / "create-requested.json").exists()


def test_existing_directory_and_later_unexpected_file_are_never_deleted(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    directory = root / ".at07-docker-cli"
    directory.mkdir()
    sentinel = directory / "do-not-delete"
    sentinel.write_bytes(b"Q-EXISTING")
    with pytest.raises(FileExistsError):
        with live._private_docker_config(root):
            pytest.fail("preexisting directory cannot be acquired")
    assert sentinel.read_bytes() == b"Q-EXISTING"
    owned_root = tmp_path / "owned"
    owned_root.mkdir()
    with pytest.raises(OSError):
        with live._private_docker_config(owned_root) as owned:
            (owned / "unexpected").write_bytes(b"Q-PRESERVE")
    assert (owned_root / ".at07-docker-cli/unexpected").read_bytes() == b"Q-PRESERVE"


@pytest.mark.parametrize("failure", ["exit", "oserror", "timeout", "oversized"])
def test_failed_observation_has_bounded_secret_free_error_without_retry(tmp_path, monkeypatch, failure, capsys):
    directory = tmp_path / ".at07-docker-cli"
    directory.mkdir()
    calls = []
    secret = "Q-SYNTHETIC-TOKEN-DO-NOT-EMIT"

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        if failure == "oserror":
            raise OSError(secret)
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 10, output=secret, stderr=secret)
        return SimpleNamespace(returncode=1 if failure == "exit" else 0,
            stdout=secret * 20000 if failure == "oversized" else secret, stderr=secret)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises((RuntimeError, ValueError)) as error:
        live.docker_read("ps", "-aq", "--no-trunc", configuration=configuration().docker_export,
            private_config=directory)
    assert str(error.value) in {"docker_read_failed", "docker_observation_limit"}
    assert secret not in str(error.value) and len(calls) == 1
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("failure", ["sdk_unknown", "postcreate_unknown"])
def test_execute_keeps_every_observation_on_one_endpoint_and_never_replays(tmp_path, monkeypatch, endpoint, failure):
    """Original create/finish run against intercepted SDK and transport seams.

    Diagnostic step results are incomplete mocks, then an unknown is injected;
    no successful isolation verdict or candidate execution is fabricated.
    """
    config = configuration(endpoint)
    root = prepared(tmp_path, config)
    key = root / "synthetic-key"
    key.write_text("Q-SYNTHETIC-KEY-NOT-REAL")
    (root / "canary").mkdir()
    (root / "canary/credentials").write_bytes(b"AT07-SYNTHETIC-NOT-A-SECRET\n")
    reads = spy_key(monkeypatch, key)
    engines, endpoints = bind_transport(monkeypatch, config)
    calls = []
    server = {"id": SERVER_ID, "image": at07.SERVER_IMAGE, "owner": "r1-at07", "state": "running"}
    target = {"id": TARGET_ID, "image": PYTHON_IMAGE, "owner": "r1-at07", "state": "running", "ip": "172.17.0.2"}
    main = {"id": MAIN_ID, "probe": root.name, "image": config.environment.image,
        "privileged": False, "cpu": 1000000000, "memory": 536870912, "pids": 128,
        "caps_drop": ["ALL"], "caps_add": [], "security": ["no-new-privileges"],
        "network": "container:" + SIDECAR_ID, "mounts": [{"Type": "volume",
            "Name": "opensandbox-runtime-q-sdk-id", "Destination": "/opt/opensandbox"}]}
    sidecar = {"id": SIDECAR_ID, "sidecar_for": "q-sdk-id", "image": at07.EGRESS_IMAGE,
        "privileged": False, "network": "bridge"}

    def run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs)))
        args = argv[5:]
        if args[0] == "inspect":
            mapping = {"morph-r1-at07-server": server, "morph-r1-at07-target": target,
                "sandbox-q-sdk-id": main, SIDECAR_ID: sidecar}
            output = json.dumps(mapping[args[-1]])
        elif args[0] == "exec" and args[2] == "cat":
            output = CONFIG_FILE.read_text()
        elif args[0] == "exec":
            output = json.dumps({"nftables": [{"chain": {"hook": "output", "type": "filter", "policy": "drop"}}]})
        elif args[0] == "logs":
            output = "canary.at07.test action=deny"
        elif args[0] == "ps" and "--filter" in args:
            output = SIDECAR_ID
        else:
            output = "\n".join((SERVER_ID, TARGET_ID)) if args[0] == "ps" else ""
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    controls = []

    def target_control():
        controls.append(True)
        return {"dns_positive": True, "canary_exists": True, "fake_credential_present": True,
            "denied_tcp_hits": 0, "dns_queries": len(controls)}

    monkeypatch.setattr(live, "target_control", target_control)
    sdk = SimpleNamespace(id="q-sdk-id", close=Mock(), kill=Mock(),
        get_info=lambda: SimpleNamespace(model_dump=lambda **kwargs: {
            "id": "q-sdk-id", "expires_at": "2000-01-01T00:00:00+00:00"}),
        get_egress_policy=lambda: SimpleNamespace(model_dump=lambda **kwargs: {"default_action": "deny", "egress": []}))

    def sdk_create(*args, **kwargs):
        assert len(engines) == 2, "observer and original create preflights must both run"
        assert len(reads) == 1
        if failure == "sdk_unknown":
            raise TimeoutError("Q-SYNTHETIC-SDK-UNKNOWN")
        return sdk

    create = Mock(side_effect=sdk_create)
    monkeypatch.setattr(at07.SandboxSync, "create", create)

    def step(session, result, directory, name):
        assert isinstance(session, OpenSandboxSession) and session.owned
        if name == "cpu":
            raise TimeoutError("Q-SYNTHETIC-OBSERVATION-UNKNOWN")
        return result.model_copy(update={"observations": {**result.observations,
            name: {"exit_code": 0, "error": None, "data": {}}}})

    monkeypatch.setattr(live, "run_step", step)
    monkeypatch.setattr(live, "check_exports", lambda session, result, directory:
        result.model_copy(update={"observations": {**result.observations, "export": {
            "small": True, "large": "artifact_size_limit", "absolute": "artifact_path_escape",
            "traversal": "artifact_path_escape", "symlink": "artifact_path_escape",
            "frozen_export": True}}}))
    result = execute(root, key)
    assert "TimeoutError" in result.reasons and "ValueError" not in result.reasons
    assert create.call_count == 1 and len(reads) == 1
    assert endpoints == [endpoint, endpoint] and all(e.closed == 1 for e in engines)
    assert result.remote_effect == "unknown"
    assert any(v != "passed" for v in at07.review(result).values())
    assert json.loads((root / "review.json").read_bytes())["verified"] is False
    assert (root / "create-requested.json").exists()
    assert not (root / ".at07-docker-cli").exists()
    for argv, options in calls:
        assert argv[:5] == ["docker", "--host", endpoint, "--config", str(root / ".at07-docker-cli")]
        assert options["shell"] is False and options["timeout"] == 10
        assert set(options["env"]) <= {"PATH", "SYSTEMROOT", "WINDIR"}
    if failure == "sdk_unknown":
        assert result.sandbox_id is None and result.cleanup_state == "unknown"
        assert sdk.kill.call_count == sdk.close.call_count == 0
        assert "create_or_readiness_unknown" in result.reasons
    else:
        assert {argv[5] for argv, _ in calls} == {"inspect", "exec", "ps", "volume", "network", "logs"}
        assert any(argv[5:] == ["exec", SERVER_ID, "cat", "/etc/opensandbox/config.toml"] for argv, _ in calls)
        assert any(argv[5:] == ["exec", SIDECAR_ID, "nft", "-j", "list", "ruleset"] for argv, _ in calls)
        assert sdk.kill.call_count == sdk.close.call_count == 1
    original_calls = len(calls)
    with pytest.raises(FileExistsError, match="original_probe_is_not_replayable"):
        execute(root, key)
    assert create.call_count == 1 and len(reads) == 1 and len(calls) == original_calls
