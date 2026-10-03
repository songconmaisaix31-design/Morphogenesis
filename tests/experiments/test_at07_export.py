"""Inert official-session filesystem boundary; no code, process or network runs."""

import os
import socket
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from orchestration.experiments.backend import OpenSandboxSession


@pytest.fixture(autouse=True)
def deny_process_and_network(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("AT07 offline tests forbid processes/network")
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(os, "system", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


def session_with_files(*, link=None, size=4):
    files = Mock()
    def listing(entry):
        children = {"/": "/tmp", "/tmp": "/tmp/morph-research",
                    "/tmp/morph-research": "/tmp/morph-research/result.bin"}
        name = children[entry.path]
        kind = "symlink" if name == link else ("file" if name.endswith(".bin") else "directory")
        return [SimpleNamespace(path=name, entry_type=kind, size=size)]
    files.list_directory.side_effect = listing
    files.read_bytes_stream.return_value = iter([b"safe"])
    return OpenSandboxSession(SimpleNamespace(id="inert", files=files), owned=True), files


@pytest.mark.parametrize("path", ["/tmp/outside", "/tmp/morph-research/../outside",
    "/tmp/morph-research/sub/../../outside", "/etc/passwd", "/tmp/morph-research//result.bin"])
def test_export_path_escape_rejected_before_sdk(path):
    session, files = session_with_files()
    with pytest.raises(PermissionError, match="artifact_path_escape"):
        session.download(path, 64)
    files.read_bytes_stream.assert_not_called()


@pytest.mark.parametrize("link", ["/tmp", "/tmp/morph-research", "/tmp/morph-research/result.bin"])
def test_export_rejects_symlink_in_every_path_component(link):
    session, files = session_with_files(link=link)
    with pytest.raises(PermissionError, match="artifact_path_escape"):
        session.download("/tmp/morph-research/result.bin", 64)
    files.read_bytes_stream.assert_not_called()


def test_bounded_normal_file_reaches_sdk_stream():
    session, files = session_with_files()
    assert session.download("/tmp/morph-research/result.bin", 64) == b"safe"
    files.read_bytes_stream.assert_called_once_with("/tmp/morph-research/result.bin", range_header="bytes=0-64")


def test_oversize_stream_still_rejected_if_metadata_understates_size():
    session, files = session_with_files(size=1)
    files.read_bytes_stream.return_value = iter([b"x" * 65])
    with pytest.raises(ValueError, match="artifact_size_limit"):
        session.download("/tmp/morph-research/result.bin", 64)


def test_unknown_file_type_is_unsupported_without_export():
    session, files = session_with_files()
    files.list_directory.return_value = [SimpleNamespace(path="/tmp", entry_type=None, size=0)]
    files.list_directory.side_effect = None
    with pytest.raises(ValueError, match="bounded_export_metadata_unsupported"):
        session.download("/tmp/morph-research/result.bin", 64)
    files.read_bytes_stream.assert_not_called()


@pytest.mark.parametrize("leaf_type", ["file", "symlink", None])
def test_official_sdk_directory_types_and_bounded_download_wire(leaf_type):
    import httpx
    from opensandbox.config import ConnectionConfigSync
    from opensandbox.models.sandboxes import SandboxEndpoint
    from opensandbox.sync.adapters.filesystem_adapter import FilesystemAdapterSync

    requests = []
    children = {"/": "/tmp", "/tmp": "/tmp/morph-research", "/tmp/morph-research": "/tmp/morph-research/result.bin"}
    def respond(request):
        requests.append(request)
        if request.url.path == "/directories/list":
            assert request.url.params["depth"] == "1"
            name = children[request.url.params["path"]]
            body = {"path": name, "size": 4, "mode": 600, "owner": "root", "group": "root",
                    "modified_at": "2026-10-03T00:00:00Z", "created_at": "2026-10-03T00:00:00Z"}
            kind = leaf_type if name.endswith(".bin") else "directory"
            if kind is not None:
                body["type"] = kind
            return httpx.Response(200, json=[body], request=request)
        assert request.url.path == "/files/download"
        # Execd's offset/limit query is LINE-based, not a byte limit. Use Range.
        assert "limit" not in request.url.params
        assert request.headers["Range"] == "bytes=0-64"
        return httpx.Response(200, content=b"safe", request=request)
    config = ConnectionConfigSync(transport=httpx.MockTransport(respond), use_server_proxy=True)
    files = FilesystemAdapterSync(config, SandboxEndpoint(endpoint="localhost:44772"))
    session = OpenSandboxSession(SimpleNamespace(id="inert-wire", files=files), owned=True)
    try:
        if leaf_type == "file":
            assert session.download("/tmp/morph-research/result.bin", 64) == b"safe"
            assert len(requests) == 4  # Positive must actually consume SDK bytes.
        else:
            with pytest.raises((PermissionError, ValueError)):
                session.download("/tmp/morph-research/result.bin", 64)
            assert len(requests) == 3
    finally:
        files._httpx_client.close()


def test_metadata_then_stream_cannot_certify_atomic_export_scope():
    from orchestration.experiments import at07
    from tests.experiments.test_at07 import complete_observations, configuration

    session, files = session_with_files()
    def replaced_after_inspection(*args, **kwargs):
        assert files.list_directory.call_count == 3
        # Only inert bytes: simulate another container process replacing the
        # checked regular file with a link immediately before the SDK open.
        return iter([b"fake-outside-root"])
    files.read_bytes_stream.side_effect = replaced_after_inspection
    assert session.download("/tmp/morph-research/result.bin", 64) == b"fake-outside-root"
    result = at07.At07Result(probe_id="fixture", configuration=configuration(), provenance="live",
        sandbox_id="inert", observations=complete_observations(), remote_effect="known", cleanup_state="destroyed")
    assert at07.review(result)["export"] == "unsupported"


@pytest.mark.parametrize("entry", ["admit", "create"])
def test_live_export_unsupported_cannot_be_overridden_by_filled_probe(monkeypatch, entry):
    from orchestration.experiments import sandbox_adapter as adapter
    from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
    from orchestration.experiments.trusted import TrustedProbeRegistry
    from tests.experiments.generated_helpers import GENERATED_CODE, make_context, make_poisson_plan
    from tests.experiments.test_generated_configuration import configured_backend

    plan = make_poisson_plan()
    backend, record = configured_backend(plan)  # Complete, matched, filled passed/verified record.
    calls = []
    monkeypatch.setattr(adapter.SandboxSync, "create", lambda *a, **k: calls.append((a, k)))
    report = backend.isolation()
    assert not report.declared.export_bounded
    assert not report.verified and report.probe != "passed"
    assert "atomic_export_scope_unsupported" in report.reasons
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry((record,)))
    prepared = executor.prepare(plan, {"experiment.py": GENERATED_CODE.encode()})
    with pytest.raises(ValueError, match="isolation_capability_incomplete"):
        if entry == "admit":
            executor.admit(prepared)
        else:
            backend.create(plan, make_context())
    assert calls == []


def test_prepared_full_probe_cannot_survive_export_support_downgrade(monkeypatch):
    from orchestration.experiments import sandbox_adapter as adapter
    from orchestration.experiments.generated_executor import GeneratedExperimentExecutor
    from orchestration.experiments.trusted import TrustedProbeRegistry
    from tests.experiments.generated_helpers import GENERATED_CODE, make_poisson_plan
    from tests.experiments.test_generated_configuration import configured_backend

    plan = make_poisson_plan()
    backend, record = configured_backend(plan)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry((record,)))
    # A test-only hypothetical implementation; never an environment/config knob.
    monkeypatch.setattr(adapter, "ATOMIC_EXPORT_SCOPE_SUPPORTED", True)
    prepared = executor.prepare(plan, {"experiment.py": GENERATED_CODE.encode()})
    executor.admit(prepared)
    monkeypatch.setattr(adapter, "ATOMIC_EXPORT_SCOPE_SUPPORTED", False)
    with pytest.raises(ValueError, match="prepared_configuration_changed"):
        executor.admit(prepared)
