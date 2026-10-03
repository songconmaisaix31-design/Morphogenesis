"""Inert Engine + official lifecycle boundary; no sandbox/process/network runs."""

import base64
from copy import deepcopy
import io
import json
import os
from pathlib import PurePosixPath
import socket
import subprocess
import tarfile
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from opensandbox.config import ConnectionConfigSync

from orchestration.experiments import frozen_export as module
from orchestration.experiments.backend import OpenSandboxSession
from orchestration.experiments.generated import DockerExportConfiguration
from tests.experiments.test_at07 import configuration

MAIN, SIDECAR = "2" * 64, "3" * 64
PATH = "/tmp/morph-research/result.bin"


@pytest.fixture(autouse=True)
def deny_execution(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("frozen-export tests forbid processes/network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket.socket, "sendto", denied)


def export_config():
    return DockerExportConfiguration(endpoint="npipe:////./pipe/dockerDesktopLinuxEngine",
        daemon_id="inert-daemon-1", engine_version="29.5.3")


def tar_bytes(*, name="result.bin", body=b"safe", kind=tarfile.REGTYPE, link="", extra=False, pax=None):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.PAX_FORMAT) as archive:
        member = tarfile.TarInfo(name)
        member.type, member.linkname = kind, link
        member.size = len(body) if kind == tarfile.REGTYPE else 0
        member.pax_headers = pax or {}
        archive.addfile(member, io.BytesIO(body))
        if extra:
            archive.addfile(tarfile.TarInfo("extra.bin"), io.BytesIO())
    return stream.getvalue()


class Response:
    def __init__(self, body=b"", headers=None, status=200):
        self.body = io.BytesIO(body)
        self.headers = headers or {}
        self.status_code = status
        self.raw = SimpleNamespace(read1=lambda n, **kw: self.body.read1(n))
        self.closed = False

    def close(self):
        self.closed = True


class Daemon:
    def __init__(self, config):
        self.config = config
        self.requests, self.responses, self.events = [], [], []
        self.preflight_changes = {}
        self.nodes = {"/tmp": 1 << 31, "/tmp/morph-research": 1 << 31, PATH: 0}
        self.archive = tar_bytes()
        self.size = 4
        self.blocked_replacements = 0
        self.replace_on_read = False
        self.pause_error = False
        self.resume_error = False
        self.volume_users = [{"Id": MAIN}, {"Id": SIDECAR}]
        self.volume_options = None
        self.sidecar = {"Id": SIDECAR, "State": {"Running": True, "Paused": False},
            "Config": {"Image": module.EGRESS_IMAGE, "Labels": {"opensandbox.io/egress-sidecar-for": "sid"}},
            "HostConfig": {"Privileged": False}, "Mounts": [{"Type": "volume", "Name": "opensandbox-runtime-sid",
                "Destination": "/opt/opensandbox", "RW": True}]}
        self.main = {"Id": MAIN, "State": {"Running": True, "Paused": False},
            "Config": {"Image": config.environment.image, "Labels": {"opensandbox.io/id": "sid"}},
            "HostConfig": {"Privileged": False, "CapAdd": [], "CapDrop": ["ALL"],
                "SecurityOpt": ["no-new-privileges=true"], "PidMode": "", "Devices": [], "VolumesFrom": [],
                "NetworkMode": "container:" + SIDECAR, "NanoCpus": 1000000000, "Memory": 536870912,
                "PidsLimit": config.resources.process_limit},
            "Mounts": [{"Type": "volume", "Name": "opensandbox-runtime-sid", "Destination": "/opt/opensandbox", "RW": True}]}

    def set_paused(self, value):
        self.main["State"]["Paused"] = self.sidecar["State"]["Paused"] = value

    def request(self, method, url, **options):
        assert method in {"GET", "HEAD"} and options["allow_redirects"] is False
        assert options["headers"] == {"Accept-Encoding": "identity"}
        assert 0 < options["timeout"] <= 10
        route = url.split("/v1.52", 1)[1]
        self.requests.append((method, route, deepcopy(options)))
        if route == "/version":
            value = {"Version": "29.5.3", "Os": "linux", **self.preflight_changes}
        elif route == "/info":
            value = {"ID": "inert-daemon-1", "OSType": "linux", **self.preflight_changes}
        elif route == "/containers/json":
            assert json.loads(options["params"]["filters"]) == {"volume": ["opensandbox-runtime-sid"]}
            value = self.volume_users
        elif route == "/volumes/opensandbox-runtime-sid":
            value = {"Name": "opensandbox-runtime-sid", "Driver": "local", "Scope": "local",
                "Options": self.volume_options, "Labels": {"opensandbox.io/volume-managed-by": "server"}}
        elif route.endswith("/" + self.config.instance_id + "/json"):
            value = {"Id": self.config.instance_id, "State": {"Running": True},
                "Config": {"Image": module.SERVER_IMAGE}, "NetworkSettings": {"Ports": {
                    "8090/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8099"}]}}}
        elif route in {"/containers/" + MAIN + "/json", "/containers/sandbox-sid/json"}:
            value = self.main
        elif route == "/containers/" + SIDECAR + "/json":
            value = self.sidecar
        else:
            assert route == "/containers/" + MAIN + "/archive"
            path = options["params"]["path"]
            mode = self.nodes[path]
            stat = {"name": PurePosixPath(path).name, "size": self.size if path == PATH else 4096,
                "mode": mode, "mtime": "2026-10-03T00:00:00Z", "linkTarget": "/fake/outside" if mode == 1 << 27 else ""}
            if method == "GET" and self.replace_on_read:
                if self.main["State"]["Paused"]:
                    self.blocked_replacements += 1
                else:
                    self.archive = tar_bytes(body=b"fake-outside")
            response = Response(self.archive if method == "GET" else b"",
                {"X-Docker-Container-Path-Stat": base64.b64encode(json.dumps(stat).encode()).decode()})
            self.responses.append(response)
            return response
        response = Response(json.dumps(value).encode())
        self.responses.append(response)
        return response

    def close(self):
        self.events.append("transport_closed")


class Sandbox:
    id = "sid"
    connection_config = ConnectionConfigSync(domain="127.0.0.1:8099")

    def __init__(self, daemon):
        self.daemon = daemon

    def pause(self):
        self.daemon.events.append("pause")
        if self.daemon.pause_error:
            raise TimeoutError("inert disconnected pause")
        self.daemon.set_paused(True)

    def close(self):
        self.daemon.events.append("sdk_closed")

    def kill(self):
        self.daemon.events.append("kill:sid")


def fixture(monkeypatch):
    config = configuration().model_copy(update={"docker_export": export_config()})
    daemon = Daemon(config)
    monkeypatch.setattr(module, "_transport", lambda endpoint: (daemon, "http+docker://localnpipe"))
    control = module.FrozenDockerExport(config)
    def resume(sid, **kwargs):
        assert sid == "sid" and kwargs["resume_timeout"].total_seconds() == 10
        daemon.events.append("resume:sid")
        if daemon.resume_error:
            raise TimeoutError("inert disconnected resume")
        daemon.set_paused(False)
        return Sandbox(daemon)
    monkeypatch.setattr("orchestration.experiments.backend.SandboxSync.resume", resume)
    return OpenSandboxSession(Sandbox(daemon), owned=True, export_control=control), daemon


def test_paused_ancestor_and_archive_reads_block_replacement_and_preserve_bytes(monkeypatch):
    session, daemon = fixture(monkeypatch)
    session.export_control.preflight()
    daemon.replace_on_read = True
    assert session.download(PATH, 64) == b"safe"
    assert daemon.blocked_replacements == 1 and daemon.events == ["pause", "resume:sid", "sdk_closed"]
    methods = [m for m, p, _ in daemon.requests if p.endswith("/archive")]
    assert methods == ["HEAD", "HEAD", "HEAD", "GET"]
    assert all(r.closed for r in daemon.responses)
    assert session.export_control.observations[0]["paused_after"] is True
    session.destroy()
    session.close()
    assert daemon.events[-3:] == ["kill:sid", "sdk_closed", "transport_closed"]


@pytest.mark.parametrize("path", ["/tmp", "/tmp/morph-research", PATH])
@pytest.mark.parametrize("kind", [1 << 27, 1 << 25, 1 << 19])
def test_each_ancestor_and_leaf_reject_link_fifo_or_irregular(monkeypatch, path, kind):
    session, daemon = fixture(monkeypatch)
    daemon.nodes[path] = kind
    with pytest.raises(PermissionError, match="artifact_path_escape_or_type"):
        session.download(PATH, 64)
    assert not any(m == "GET" and p.endswith("/archive") for m, p, _ in daemon.requests)
    assert daemon.main["State"]["Paused"] is False


@pytest.mark.parametrize("change", ["mount", "shared", "privilege", "caps", "id", "image", "resources"])
def test_actual_isolation_mismatch_rejects_before_pause(monkeypatch, change):
    session, daemon = fixture(monkeypatch)
    if change == "mount":
        daemon.main["Mounts"][0]["Destination"] = "/tmp"
    elif change == "shared":
        daemon.main["HostConfig"]["VolumesFrom"] = ["unrelated"]
    elif change == "privilege":
        daemon.main["HostConfig"]["Privileged"] = True
    elif change == "caps":
        daemon.main["HostConfig"]["CapAdd"] = ["SYS_ADMIN"]
    elif change == "id":
        daemon.main["Config"]["Labels"]["opensandbox.io/id"] = "other"
    elif change == "image":
        daemon.main["Config"]["Image"] = "other"
    else:
        daemon.main["HostConfig"]["PidsLimit"] = 0
    with pytest.raises(PermissionError):
        session.download(PATH, 64)
    assert "pause" not in daemon.events


@pytest.mark.parametrize("bad", ["link", "hardlink", "extra", "outside", "metadata", "header", "truncated", "size", "stream"])
def test_bad_archive_or_size_is_rejected_without_extraction(monkeypatch, bad):
    session, daemon = fixture(monkeypatch)
    choices = {"link": tar_bytes(kind=tarfile.SYMTYPE, link="/fake/outside"),
        "hardlink": tar_bytes(kind=tarfile.LNKTYPE, link="/fake/outside"), "extra": tar_bytes(extra=True),
        "outside": tar_bytes(name="../outside"), "metadata": tar_bytes(pax={"path": "result.bin"}),
        "header": b"invalid" * 512, "truncated": tar_bytes()[:1024], "size": tar_bytes(body=b"x" * 65),
        "stream": b"x" * 70000}
    daemon.archive = choices[bad]
    with pytest.raises((PermissionError, ValueError, tarfile.TarError)):
        session.download(PATH, 64)
    assert daemon.main["State"]["Paused"] is False
    assert session.export_control.observations == []


@pytest.mark.parametrize("fault", ["pause", "resume"])
def test_unknown_lifecycle_is_never_replayed(monkeypatch, fault):
    session, daemon = fixture(monkeypatch)
    setattr(daemon, fault + "_error", True)
    with pytest.raises(module.ExportUnknown):
        session.download(PATH, 64)
    first = list(daemon.events)
    with pytest.raises(module.ExportUnknown, match="previous_export_effect_unknown"):
        session.download(PATH, 64)
    assert daemon.events == first
    assert daemon.events.count("pause") == 1 and daemon.events.count("resume:sid") <= 1


def test_attached_session_never_pauses_or_exports(monkeypatch):
    session, daemon = fixture(monkeypatch)
    session.owned = False
    with pytest.raises(PermissionError, match="attached_session"):
        session.download(PATH, 64)
    assert not daemon.requests and not daemon.events


@pytest.mark.parametrize("change", [{"Version": "29.5.4"}, {"ID": "other-daemon"}, {"OSType": "windows"}])
def test_engine_binding_preflight_refuses_changed_identity(monkeypatch, change):
    session, daemon = fixture(monkeypatch)
    daemon.preflight_changes = change
    with pytest.raises(PermissionError, match="daemon_mismatch"):
        session.export_control.preflight()
    assert "pause" not in daemon.events


def test_transport_deadline_and_oversized_response_close(monkeypatch):
    session, daemon = fixture(monkeypatch)
    response = Response(b"x")
    monkeypatch.setattr(module.time, "monotonic", lambda: 11)
    with pytest.raises(module.ExportUnknown, match="deadline"):
        session.export_control._bytes(response, 1, 10)
    with pytest.raises(ValueError, match="stream_limit"):
        session.export_control._bytes(Response(b"too large"), 1, 20)


def test_benign_pax_time_is_read_as_bytes_and_never_extracted():
    assert module._tar_file(tar_bytes(pax={"mtime": "1700.25"}), "result.bin", 4, 64) == b"safe"


def test_unconfigured_and_remote_engine_control_are_refused():
    with pytest.raises(ValueError):
        module.FrozenDockerExport(configuration())
    with pytest.raises(ValueError):
        export_config().model_validate({**export_config().model_dump(), "endpoint": "tcp://remote:2375"})
    with pytest.raises(ValueError):
        export_config().model_validate({**export_config().model_dump(), "engine_version": "29.5.4"})


@pytest.mark.parametrize("change", ["third_writer", "driver_bind", "unknown_rw", "sidecar_mount"])
def test_fixed_runtime_volume_exception_never_accepts_other_writers(monkeypatch, change):
    session, daemon = fixture(monkeypatch)
    if change == "third_writer":
        daemon.volume_users.append({"Id": "4" * 64})
    elif change == "driver_bind":
        daemon.volume_options = {"type": "none", "o": "bind", "device": "/host"}
    elif change == "unknown_rw":
        del daemon.main["Mounts"][0]["RW"]
    else:
        daemon.sidecar["Mounts"][0]["Destination"] = "/tmp"
    with pytest.raises(PermissionError):
        session.download(PATH, 64)
    assert "pause" not in daemon.events


def test_resume_identity_substitution_cannot_change_cleanup_target(monkeypatch):
    session, daemon = fixture(monkeypatch)
    other = Mock(id="unrelated")
    monkeypatch.setattr("orchestration.experiments.backend.SandboxSync.resume", lambda *a, **kw: other)
    with pytest.raises(module.ExportUnknown):
        session.download(PATH, 64)
    session.destroy()
    other.kill.assert_not_called()
    other.close.assert_called_once()
    assert daemon.events[-1] == "kill:sid"


def test_official_transport_constructs_without_engine_or_docker_auth(monkeypatch):
    import docker.auth
    import docker.utils.config

    def denied(*args, **kwargs):
        raise AssertionError("Docker account config is unnecessary for export")
    monkeypatch.setattr(docker.auth, "load_config", denied)
    monkeypatch.setattr(docker.utils.config, "load_general_config", denied)
    endpoints = ["unix:///var/run/docker.sock"]
    if os.name == "nt":
        endpoints.append("npipe:////./pipe/dockerDesktopLinuxEngine")
    for endpoint in endpoints:
        transport, base = module._transport(endpoint)
        try:
            assert transport.trust_env is False and base.startswith("http+docker://")
            adapter = transport.adapters["http+docker://"]
            assert adapter.timeout == 10 and len(adapter.pools) == 0
            if endpoint.startswith("unix"):
                assert adapter.socket_path == "/var/run/docker.sock"
            else:
                assert adapter.npipe_path == "//./pipe/dockerDesktopLinuxEngine"
        finally:
            transport.close()
