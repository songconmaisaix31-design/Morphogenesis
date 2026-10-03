"""Read-only official Docker transport for a paused original OpenSandbox session.

The SDK owns pause/resume/kill. This adapter never executes container code or
mutates Engine state. It consumes one bounded tar file without host extraction.
The host controls the daemon; a candidate never receives this transport.
"""

from __future__ import annotations

import base64
from importlib import import_module
import io
import json
from pathlib import PurePosixPath
import re
import tarfile
import time
from typing import Any, cast
from urllib.parse import urlsplit

from orchestration.experiments.generated import IsolationConfiguration

DIRECTORY = PurePosixPath("/tmp/morph-research")
SERVER_IMAGE = "opensandbox/server:release-1.1.0@sha256:68ca0212a2749b2c73096ce2ec0264455c64442c45f81007db442f52bf84c9d1"
EGRESS_IMAGE = "opensandbox/egress:v1.1.7@sha256:db7345d567b0970f384b8e3fa7a93a71b7f43d4b16bb2009de34096e9a87b3b5"
_MODE_DIR = 1 << 31  # Docker PathStat uses Go FileMode, not POSIX st_mode.
_MODE_TYPE = sum(1 << bit for bit in (31, 27, 26, 25, 24, 21, 19))


def _transport(endpoint: str) -> tuple[Any, str]:
    # APIClient.__init__ reads Docker auth configuration. We only need its
    # official npipe/unix transport, and never need registry/account credentials.
    session = import_module("requests").Session()
    session.trust_env = False
    module = import_module("docker.transport")
    if endpoint.startswith("npipe://"):
        adapter = module.NpipeHTTPAdapter(endpoint, timeout=10, pool_connections=1, max_pool_size=1)
        base = "http+docker://localnpipe"
    else:
        adapter = module.UnixHTTPAdapter(endpoint.replace("unix://", "http+unix://", 1),
                                         timeout=10, pool_connections=1, max_pool_size=1)
        base = "http+docker://localhost"
    session.mount("http+docker://", adapter)
    return session, base


class ExportUnknown(TimeoutError):
    """Control-plane state/transport uncertain: preserve unknown, never retry."""


def export_path(path: str, limit: int) -> PurePosixPath:
    candidate = PurePosixPath(path)
    if (not path.startswith(str(DIRECTORY) + "/") or "\\" in path or "\0" in path
            or any(part in {"", ".", ".."} for part in path.split("/")[1:])
            or not candidate.is_relative_to(DIRECTORY) or len(path.encode()) > 1024):
        raise PermissionError("artifact_path_escape")
    if type(limit) is not int or not 1 <= limit <= 16777216:
        raise ValueError("artifact_size_limit")
    return candidate


def _tar_file(raw: bytes, name: str, expected_size: int, limit: int) -> bytes:
    """Use the standard parser, with bounded input and no extraction APIs."""
    if len(raw) > limit + 65536:
        raise ValueError("archive_size_limit")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        member = archive.next()
        if (member is None or not member.isfile() or member.name != name
                or member.linkname or member.size != expected_size or member.size > limit
                or member.offset_data > 16384):
            raise PermissionError("artifact_archive_member_rejected")
        # PAX may carry mtime/atime from official Go archives. It may not replace
        # paths/size/types or supply unbounded metadata. Nothing is extracted.
        if any(k not in {"mtime", "atime", "ctime"} for k in member.pax_headers):
            raise PermissionError("artifact_archive_metadata_rejected")
        stream = archive.extractfile(member)
        if stream is None:
            raise ValueError("artifact_archive_missing_data")
        with stream:
            body = stream.read(limit + 1)
        if len(body) != expected_size or len(body) > limit:
            raise ValueError("artifact_size_limit")
        end = member.offset_data + ((member.size + 511) // 512) * 512
        if len(raw) < end + 1024 or any(raw[end:]):
            raise PermissionError("artifact_archive_extra_or_truncated")
        if archive.next() is not None:
            raise PermissionError("artifact_archive_extra_member")
        return body


class FrozenDockerExport:
    """One SDK session's exact Engine control-plane binding; no lifecycle owner."""

    def __init__(self, configuration: IsolationConfiguration) -> None:
        self.configuration = IsolationConfiguration.model_validate_json(configuration.model_dump_json())
        config = self.configuration.docker_export
        if config is None:
            raise ValueError("frozen_export_configuration_required")
        self.api, base = _transport(config.endpoint)
        self.base_url = base + "/v" + config.api_version
        self.deadline: float | None = None
        self.main_id: str | None = None
        self.sidecar_id: str | None = None
        self.sandbox_id: str | None = None
        self.observations: list[dict[str, Any]] = []

    def close(self) -> None:
        self.api.close()

    def _response(self, method: str, path: str, *, params: dict[str, str] | None = None) -> Any:
        remaining = 10.0 if self.deadline is None else min(10.0, self.deadline - time.monotonic())
        if remaining <= 0:
            raise ExportUnknown("docker_export_deadline")
        try:
            response = self.api.request(method, self.base_url + path, params=params,
                headers={"Accept-Encoding": "identity"}, timeout=remaining, stream=True,
                allow_redirects=False)
        except Exception as error:
            raise ExportUnknown("docker_export_transport_unknown") from error
        if response.status_code != 200:
            response.close()
            raise ExportUnknown("docker_export_control_response_unknown")
        return response

    def _json(self, path: str) -> dict[str, Any]:
        response = self._response("GET", path)
        try:
            raw = self._bytes(response, 262144, self.deadline or time.monotonic() + 10)
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("docker_export_object_required")
            return value
        finally:
            response.close()

    @staticmethod
    def _bytes(response: Any, limit: int, deadline: float) -> bytes:
        data = bytearray()
        try:
            while True:
                if time.monotonic() > deadline:
                    raise ExportUnknown("docker_export_deadline")
                # read1 performs at most one underlying buffered read. A full
                # iter_content chunk can hide an arbitrarily slow byte trickle.
                chunk = response.raw.read1(16384, decode_content=False)
                if time.monotonic() > deadline:
                    raise ExportUnknown("docker_export_deadline")
                if not chunk:
                    break
                if len(data) + len(chunk) > limit:
                    raise ValueError("docker_export_stream_limit")
                data.extend(chunk)
        except (ValueError, ExportUnknown):
            raise
        except Exception as error:
            raise ExportUnknown("docker_export_stream_unknown") from error
        return bytes(data)

    def _inspect(self, identifier: str) -> dict[str, Any]:
        if re.fullmatch(r"[a-f0-9]{64}", identifier) is None:
            raise PermissionError("exact_docker_container_id_required")
        value = self._json("/containers/" + identifier + "/json")
        if value.get("Id") != identifier:
            raise PermissionError("docker_export_container_changed")
        return value

    def preflight(self) -> None:
        config = self.configuration.docker_export
        assert config is not None
        version = self._json("/version")
        info = self._json("/info")
        if (version.get("Version") != config.engine_version or info.get("ID") != config.daemon_id
                or info.get("OSType") != "linux" or version.get("Os") != "linux"):
            raise PermissionError("docker_export_daemon_mismatch")
        server = self._inspect(self.configuration.instance_id)
        endpoint = urlsplit(self.configuration.endpoint)
        ports = server.get("NetworkSettings", {}).get("Ports", {}).get("8090/tcp", []) or []
        if (server.get("Config", {}).get("Image") != SERVER_IMAGE or endpoint.scheme != "http"
                or endpoint.hostname not in {"127.0.0.1", "localhost"}
                or not server.get("State", {}).get("Running")
                or not any(p.get("HostIp") == "127.0.0.1" and p.get("HostPort") == str(endpoint.port) for p in ports)):
            raise PermissionError("docker_export_service_binding_mismatch")

    def bind(self, sandbox_id: str) -> None:
        if self.sandbox_id is not None or re.fullmatch(r"[A-Za-z0-9_-]{1,120}", sandbox_id) is None:
            raise PermissionError("fresh_export_binding_required")
        # A known successful SDK create supplies this ID; never use candidate IDs.
        main = self._json("/containers/sandbox-" + sandbox_id + "/json")
        identifier = main.get("Id", "")
        if re.fullmatch(r"[a-f0-9]{64}", identifier) is None:
            raise PermissionError("exact_docker_container_id_required")
        sidecar = str(main.get("HostConfig", {}).get("NetworkMode", "")).removeprefix("container:")
        self.main_id, self.sidecar_id, self.sandbox_id = identifier, sidecar, sandbox_id
        self.inspect_bound(paused=False)

    def inspect_bound(self, *, paused: bool | None = None) -> bool:
        if self.main_id is None or self.sidecar_id is None or self.sandbox_id is None:
            raise PermissionError("docker_export_not_bound")
        main, sidecar = self._inspect(self.main_id), self._inspect(self.sidecar_id)
        host = main.get("HostConfig", {})
        labels = main.get("Config", {}).get("Labels", {}) or {}
        mounts = main.get("Mounts", [])
        side_mounts = sidecar.get("Mounts", [])
        p = self.configuration.resources
        if (labels.get("opensandbox.io/id") != self.sandbox_id
                or main.get("Config", {}).get("Image") != self.configuration.environment.image
                or host.get("Privileged") is not False or host.get("CapAdd")
                or "ALL" not in (host.get("CapDrop") or [])
                or not any(v in {"no-new-privileges", "no-new-privileges=true"} for v in (host.get("SecurityOpt") or []))
                or host.get("PidMode") not in ("", "private") or host.get("Devices") or host.get("VolumesFrom")
                or host.get("NetworkMode") != "container:" + self.sidecar_id
                or host.get("NanoCpus") != p.cpu * 1000000000 or host.get("Memory") != p.memory_mib * 1048576
                or host.get("PidsLimit") != p.process_limit or len(mounts) != 1
                or mounts[0].get("Type") != "volume" or mounts[0].get("Name") != "opensandbox-runtime-" + self.sandbox_id
                or mounts[0].get("Destination") != "/opt/opensandbox" or mounts[0].get("RW") is not True
                or sidecar.get("Config", {}).get("Image") != EGRESS_IMAGE
                or sidecar.get("HostConfig", {}).get("Privileged") is not False
                or len(side_mounts) != 1 or any(side_mounts[0].get(key) != mounts[0].get(key)
                    for key in ("Type", "Name", "Destination", "RW"))
                or (sidecar.get("Config", {}).get("Labels", {}) or {}).get("opensandbox.io/egress-sidecar-for") != self.sandbox_id):
            raise PermissionError("docker_export_effective_isolation_mismatch")
        # Fixed upstream shares this RW runtime volume only between the owned
        # pair, outside the export tree. Both are frozen; no third writer/bind
        # driver is accepted. The export tree itself has no shared mounts.
        volume_name = "opensandbox-runtime-" + self.sandbox_id
        volume = self._json("/volumes/" + volume_name)
        if (volume.get("Name") != volume_name or volume.get("Driver") != "local"
                or volume.get("Scope") != "local" or volume.get("Options")
                or (volume.get("Labels", {}) or {}).get("opensandbox.io/volume-managed-by") != "server"):
            raise PermissionError("docker_export_runtime_volume_not_exclusive")
        response = self._response("GET", "/containers/json", params={"all": "true",
            "filters": json.dumps({"volume": [volume_name]})})
        try:
            users = json.loads(self._bytes(response, 262144, self.deadline or time.monotonic() + 10))
        finally:
            response.close()
        if (not isinstance(users, list) or len(users) != 2 or not all(isinstance(v, dict) for v in users)
                or {v.get("Id") for v in users} != {self.main_id, self.sidecar_id}):
            raise PermissionError("docker_export_runtime_volume_not_exclusive")
        main_state, sidecar_state = main.get("State", {}), sidecar.get("State", {})
        if not main_state.get("Running") or not sidecar_state.get("Running"):
            raise ExportUnknown("docker_export_container_not_running")
        actual = main_state.get("Paused")
        if type(actual) is not bool or sidecar_state.get("Paused") is not actual or (paused is not None and actual is not paused):
            raise ExportUnknown("docker_export_pause_state_unknown")
        return cast(bool, actual)

    @staticmethod
    def _stat(response: Any, path: PurePosixPath, *, directory: bool, limit: int) -> dict[str, Any]:
        encoded = response.headers.get("X-Docker-Container-Path-Stat", "")
        if not isinstance(encoded, str) or len(encoded) > 8192:
            raise PermissionError("docker_export_stat_invalid")
        try:
            value = json.loads(base64.b64decode(encoded, validate=True))
        except (ValueError, TypeError) as error:
            raise PermissionError("docker_export_stat_invalid") from error
        if not isinstance(value, dict):
            raise PermissionError("docker_export_stat_invalid")
        mode, size = value.get("mode"), value.get("size")
        if (value.get("name") != path.name or type(mode) is not int or mode < 0 or mode > 0xFFFFFFFF
                or (mode & _MODE_TYPE) != (_MODE_DIR if directory else 0)
                or value.get("linkTarget") != "" or type(size) is not int or size < 0):
            raise PermissionError("artifact_path_escape_or_type")
        if not directory and size > limit:
            raise ValueError("artifact_size_limit")
        return value

    def download(self, path: str, limit: int) -> bytes:
        self.deadline = time.monotonic() + 10
        try:
            return self._download(path, limit)
        finally:
            self.deadline = None

    def _download(self, path: str, limit: int) -> bytes:
        candidate = export_path(path, limit)
        self.inspect_bound(paused=True)
        assert self.main_id is not None
        assert self.deadline is not None
        deadline = self.deadline
        route = "/containers/" + self.main_id + "/archive"
        leaf: dict[str, Any] = {}
        parent = PurePosixPath("/")
        for part in candidate.parts[1:]:
            if time.monotonic() > deadline:
                raise ExportUnknown("docker_export_deadline")
            parent /= part
            response = self._response("HEAD", route, params={"path": str(parent)})
            try:
                leaf = self._stat(response, parent, directory=parent != candidate, limit=limit)
            finally:
                response.close()
        response = self._response("GET", route, params={"path": path})
        try:
            if self._stat(response, candidate, directory=False, limit=limit) != leaf:
                raise ExportUnknown("docker_export_file_changed_while_paused")
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise PermissionError("compressed_export_not_supported")
            raw = self._bytes(response, limit + 65536, deadline)
            body = _tar_file(raw, candidate.name, leaf["size"], limit)
        finally:
            response.close()
        self.inspect_bound(paused=True)
        self.observations.append({"main_id": self.main_id, "sidecar_id": self.sidecar_id,
            "path": path, "stat": leaf, "bytes": len(body), "paused_before": True, "paused_after": True})
        return body
