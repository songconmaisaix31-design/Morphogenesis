"""Q-owned inert HTTP/SDK boundary; the production freeze/export code runs.

No owner test helper, candidate, daemon, subprocess or socket is used. Passed
probe records in the tests are deterministic host fixtures, never AT07 proof.
"""
import base64
from copy import deepcopy
import io
import json
from pathlib import PurePosixPath
import tarfile
from types import SimpleNamespace
from urllib.parse import urlsplit

from orchestration.experiments import frozen_export
from orchestration.experiments.backend import OpenSandboxSession
from orchestration.experiments.generated import DockerExportConfiguration
from opensandbox.config import ConnectionConfigSync
from opensandbox.sync.sandbox import SandboxSync

SERVER, MAIN, EGRESS = "1" * 64, "2" * 64, "3" * 64
SID = "q-captured-request-no-sandbox"
PATH = "/tmp/morph-research/nested/result.bin"
BODY = b"Q inert bytes only"


def docker_settings():
    return DockerExportConfiguration(endpoint="npipe:////./pipe/dockerDesktopLinuxEngine",
        daemon_id="q-inert-daemon", engine_version="29.5.3")


def archive_bytes(body=BODY, *, name="result.bin", kind=tarfile.REGTYPE,
                  extra=False, pax=None):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        item = tarfile.TarInfo(name)
        item.type = kind
        item.size = len(body) if kind == tarfile.REGTYPE else 0
        if kind in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
            item.linkname = "/outside"
        item.pax_headers = pax or {}
        archive.addfile(item, io.BytesIO(body))
        if extra:
            archive.addfile(tarfile.TarInfo("unexpected.bin"))
    return buffer.getvalue()


class Reply:
    status_code = 200

    def __init__(self, body=b"", headers=None):
        self.body = io.BytesIO(body)
        self.headers = headers or {}
        self.raw = SimpleNamespace(read1=lambda n, **kw: self.body.read1(n))
        self.closed = False

    def close(self):
        self.closed = True


class InertEngine:
    """Only expected read-only Engine routes; mutable facts allow negative cases."""

    def __init__(self, configuration):
        self.config = configuration
        self.events, self.requests, self.replies = [], [], []
        self.archive = archive_bytes()
        self.stat_changes, self.get_stat_changes = {}, {}
        self.stream_failure = None
        self.read_hook = None
        self.encoding = "identity"
        self.version = {"Version": "29.5.3", "Os": "linux"}
        self.info = {"ID": "q-inert-daemon", "OSType": "linux"}
        self.server = {"Id": SERVER, "State": {"Running": True},
            "Config": {"Image": frozen_export.SERVER_IMAGE}, "NetworkSettings": {"Ports": {
                "8090/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(urlsplit(configuration.endpoint).port)}]}}}
        mount = {"Type": "volume", "Name": "opensandbox-runtime-" + SID,
                 "Destination": "/opt/opensandbox", "RW": True}
        self.main = {"Id": MAIN, "State": {"Running": True, "Paused": False},
            "Config": {"Image": configuration.environment.image, "Labels": {"opensandbox.io/id": SID}},
            "HostConfig": {"Privileged": False, "CapAdd": [], "CapDrop": ["ALL"],
                "SecurityOpt": ["no-new-privileges=true"], "PidMode": "", "Devices": [],
                "VolumesFrom": [], "NetworkMode": "container:" + EGRESS,
                "NanoCpus": configuration.resources.cpu * 10**9,
                "Memory": configuration.resources.memory_mib * 1048576,
                "PidsLimit": configuration.resources.process_limit}, "Mounts": [deepcopy(mount)]}
        self.egress = {"Id": EGRESS, "State": {"Running": True, "Paused": False},
            "Config": {"Image": frozen_export.EGRESS_IMAGE,
                "Labels": {"opensandbox.io/egress-sidecar-for": SID}},
            "HostConfig": {"Privileged": False}, "Mounts": [deepcopy(mount)]}
        self.volume = {"Name": mount["Name"], "Driver": "local", "Scope": "local", "Options": None,
            "Labels": {"opensandbox.io/volume-managed-by": "server"}}
        self.users = [{"Id": MAIN}, {"Id": EGRESS}]

    def pause_pair(self, value):
        self.main["State"]["Paused"] = self.egress["State"]["Paused"] = value

    def request(self, method, url, **options):
        assert method in {"HEAD", "GET"}, "Q transport must never mutate Engine state"
        assert options["allow_redirects"] is False
        assert options["headers"] == {"Accept-Encoding": "identity"}
        assert 0 < options["timeout"] <= 10
        route = url.split("/v1.52", 1)[1]
        self.requests.append((method, route, deepcopy(options)))
        if route.endswith("/archive"):
            assert route == "/containers/" + MAIN + "/archive"
            assert self.main["State"]["Paused"] and self.egress["State"]["Paused"]
            path = options["params"]["path"]
            directory = path != PATH
            stat = {"name": PurePosixPath(path).name, "size": 4096 if directory else len(BODY),
                    "mode": (1 << 31) | 0o700 if directory else 0o600,
                    "mtime": "2026-10-03T00:00:00Z", "linkTarget": ""}
            stat.update(self.stat_changes.get(path, {}))
            if method == "GET":
                stat.update(self.get_stat_changes)
            reply = Reply(self.archive if method == "GET" else b"", {
                "X-Docker-Container-Path-Stat": base64.b64encode(json.dumps(stat).encode()).decode(),
                "Content-Encoding": self.encoding})
            if method == "GET" and (self.stream_failure or self.read_hook):
                def read(n, **kw):
                    if self.stream_failure:
                        raise self.stream_failure
                    self.read_hook()
                    return reply.body.read1(n)
                reply.raw.read1 = read
        else:
            objects = {"/version": self.version, "/info": self.info,
                "/containers/" + SERVER + "/json": self.server,
                "/containers/sandbox-" + SID + "/json": self.main,
                "/containers/" + MAIN + "/json": self.main,
                "/containers/" + EGRESS + "/json": self.egress,
                "/volumes/opensandbox-runtime-" + SID: self.volume,
                "/containers/json": self.users}
            if route == "/containers/json":
                assert options["params"]["all"] == "true"
                assert json.loads(options["params"]["filters"]) == {"volume": [self.volume["Name"]]}
            reply = Reply(json.dumps(objects[route]).encode())
        self.replies.append(reply)
        return reply

    def close(self):
        self.events.append(("transport_close", SID))


def install_engine(monkeypatch, configuration):
    engine = InertEngine(configuration)
    def transport(endpoint):
        assert endpoint == configuration.docker_export.endpoint
        return engine, "http+docker://q-inert"
    monkeypatch.setattr(frozen_export, "_transport", transport)
    return engine


class SdkHandle:
    def __init__(self, engine, identifier=SID):
        self.id, self.engine = identifier, engine
        self.connection_config = ConnectionConfigSync(domain=urlsplit(engine.config.endpoint).netloc)
        self.pause_failure = None
        self.apply_pause = True
        def forbidden(*args, **kw):
            raise AssertionError("Q never runs a candidate or calls legacy execd file download")
        self.files = SimpleNamespace(read_bytes_stream=forbidden, list_directory=forbidden)
        self.commands = SimpleNamespace(run=forbidden)

    def pause(self):
        self.engine.events.append(("pause", self.id))
        if self.apply_pause:
            self.engine.pause_pair(True)
        if self.pause_failure:
            raise self.pause_failure

    def close(self):
        self.engine.events.append(("sdk_close", self.id))

    def kill(self):
        self.engine.events.append(("kill", self.id))


def owned_session(monkeypatch, configuration, *, resume_failure=None, resumed_id=SID):
    engine = install_engine(monkeypatch, configuration)
    control = frozen_export.FrozenDockerExport(configuration)
    control.preflight()
    handle = SdkHandle(engine)
    def resume(identifier, **kwargs):
        assert identifier == SID
        assert kwargs["resume_timeout"].total_seconds() == 10
        assert kwargs["connection_config"].request_timeout.total_seconds() == 10
        assert kwargs["connection_config"].transport is None
        engine.events.append(("resume", identifier))
        if resume_failure:
            raise resume_failure
        engine.pause_pair(False)
        return SdkHandle(engine, resumed_id)
    monkeypatch.setattr(SandboxSync, "resume", resume)
    return OpenSandboxSession(handle, owned=True, export_control=control), engine
