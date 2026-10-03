"""Independent installed freeze/export negatives at actual HTTP/SDK boundaries.

All bytes and responses are trusted deterministic fixtures. No candidate is
executed, no real probe is performed, and fixtures never change capability flags.
"""
from copy import deepcopy
import json
import tarfile
from types import SimpleNamespace

import pytest

from orchestration.experiments import frozen_export as export, sandbox_adapter as adapter
from orchestration.experiments.generated import GeneratedExperimentPlan, GeneratedResult
from orchestration.experiments.generated_executor import GeneratedExperimentExecutor, read_generated_result
from orchestration.experiments.executor import _write_json, finalize_session
from orchestration.experiments.trusted import TrustedProbeRegistry
from tests.integration.r1_security.docker_export_fixture import (
    BODY, EGRESS, MAIN, PATH, SID, archive_bytes, install_engine, owned_session,
)
from tests.integration.r1_security.test_b_configured_sdk_boundary import configured, capture_create
from tests.integration.r1_security.test_b_generated_boundaries import CODE, context


@pytest.mark.parametrize("probe_kind", ["absent", "old_none_configuration", "old_export_none"])
def test_no_explicit_export_cannot_admit_or_create_even_with_old_passed_probe(monkeypatch, probe_kind):
    p, probe, options = configured()
    options["docker_export"] = None
    if probe_kind == "absent":
        options["probe"] = None
    else:
        config = None if probe_kind == "old_none_configuration" else probe.configuration.model_copy(
            update={"docker_export": None})
        options["probe"] = probe = probe.model_copy(update={"configuration": config})
    calls = capture_create(monkeypatch)
    backend = adapter.LocalCpuSandboxBackend(**options)
    report = backend.isolation()
    assert not report.verified and not report.declared.export_bounded
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry(
        records=(probe,) if options["probe"] else ()))
    preparation = executor.prepare(p, {"candidate.py": CODE})
    assert preparation.static.passed
    with pytest.raises((ValueError, PermissionError)):
        executor.admit(preparation)
    with pytest.raises((ValueError, PermissionError)):
        backend.create(p, context())
    assert calls == []


@pytest.mark.parametrize("change", ["socket", "daemon", "old_probe"])
def test_export_configuration_change_cannot_inherit_existing_probe(monkeypatch, change):
    p, probe, options = configured()
    if change == "old_probe":
        options["probe"] = probe = probe.model_copy(update={"configuration":
            probe.configuration.model_copy(update={"docker_export": None})})
    else:
        field, value = ("endpoint", "unix:///var/run/docker.sock") if change == "socket" else (
            "daemon_id", "different-inert-daemon")
        options["docker_export"] = options["docker_export"].model_copy(update={field: value})
    calls = capture_create(monkeypatch)
    backend = adapter.LocalCpuSandboxBackend(**options)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry(records=(probe,)))
    with pytest.raises((ValueError, PermissionError)):
        executor.admit(executor.prepare(p, {"candidate.py": CODE}))
    with pytest.raises((ValueError, PermissionError)):
        backend.create(p, context())
    assert calls == []


@pytest.mark.parametrize("location", ["plan", "backend", "environment"])
def test_candidate_cannot_select_docker_control_plane(location):
    p, _, options = configured()
    payload = p.model_dump(mode="json")
    target = payload if location == "plan" else payload[location]
    target["docker_export"] = options["docker_export"].model_dump(mode="json")
    with pytest.raises(ValueError):
        GeneratedExperimentPlan.model_validate(payload)


@pytest.mark.parametrize("change", ["version", "daemon", "service_port", "service_id"])
def test_actual_daemon_service_mismatch_refuses_before_official_create(monkeypatch, change):
    p, probe, options = configured()
    engine = install_engine(monkeypatch, probe.configuration)
    if change == "version":
        engine.version["Version"] = "29.5.2"
    elif change == "daemon":
        engine.info["ID"] = "another-daemon"
    elif change == "service_port":
        engine.server["NetworkSettings"]["Ports"]["8090/tcp"][0]["HostPort"] = "65533"
    else:
        engine.server["Id"] = "4" * 64
    calls = capture_create(monkeypatch)
    with pytest.raises(PermissionError):
        adapter.LocalCpuSandboxBackend(**options).create(p, context())
    assert calls == [] and not engine.events.count(("pause", SID))
    assert engine.events == [("transport_close", SID)]
    assert all(reply.closed for reply in engine.replies)


def test_regular_bounded_export_freezes_both_owned_writers_then_resumes_each_file(monkeypatch):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    first_connection = session.sandbox
    assert session.download(PATH, 1024) == BODY
    assert session.sandbox is not first_connection and session.sandbox.id == SID
    assert session.download(PATH, 1024) == BODY
    assert engine.events.count(("pause", SID)) == engine.events.count(("resume", SID)) == 2
    paths = [(method, opts["params"]["path"]) for method, route, opts in engine.requests
             if route.endswith("/archive")]
    assert paths == [("HEAD", "/tmp"), ("HEAD", "/tmp/morph-research"),
        ("HEAD", "/tmp/morph-research/nested"), ("HEAD", PATH), ("GET", PATH)] * 2
    assert len(session.export_control.observations) == 2
    assert engine.main["Mounts"][0]["RW"] is True and engine.egress["Mounts"][0]["RW"] is True
    assert not engine.main["State"]["Paused"] and not engine.egress["State"]["Paused"]
    assert all(reply.closed for reply in engine.replies)
    session.destroy()
    session.close()
    assert [event for event in engine.events if event[0] == "kill"] == [("kill", SID)]


@pytest.mark.parametrize("endpoint", ["unix:///var/run/docker.sock", "npipe:////./pipe/dockerDesktopLinuxEngine"])
def test_official_local_transport_constructs_without_environment_or_engine_connection(monkeypatch, endpoint):
    import sys
    from docker import transport

    monkeypatch.setenv("DOCKER_HOST", "tcp://unapproved.invalid:2375")
    monkeypatch.setenv("DOCKER_CONTEXT", "unapproved-context")
    monkeypatch.setenv("HTTP_PROXY", "http://unapproved.invalid:3128")
    if endpoint.startswith("npipe:") and sys.platform != "win32":
        # Official Docker 7.2.0 omits this optional Windows adapter on Linux.
        # Exercise the real rejection; this is not NPIPE construction success.
        assert not hasattr(transport, "NpipeHTTPAdapter")
        with pytest.raises(AttributeError, match="NpipeHTTPAdapter"):
            export._transport(endpoint)
        return
    api, base = export._transport(endpoint)
    try:
        actual = api.adapters["http+docker://"]
        if endpoint.startswith("npipe:"):
            assert isinstance(actual, transport.NpipeHTTPAdapter)
            assert actual.npipe_path == endpoint.removeprefix("npipe://")
            assert base == "http+docker://localnpipe"
        else:
            assert isinstance(actual, transport.UnixHTTPAdapter)
            assert actual.socket_path == endpoint.removeprefix("unix://")
            assert base == "http+docker://localhost"
        assert api.trust_env is False and api.auth is None
    finally:
        api.close()


def test_partial_pair_pause_is_unknown_and_never_reads_or_blindly_resumes(monkeypatch):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    pause = session.sandbox.pause
    def partial_pause():
        pause()
        engine.egress["State"]["Paused"] = False
    monkeypatch.setattr(session.sandbox, "pause", partial_pause)
    with pytest.raises(export.ExportUnknown):
        session.download(PATH, 1024)
    assert engine.events == [("pause", SID)]
    assert not any(route.endswith("/archive") for _, route, _ in engine.requests)
    before = len(engine.requests)
    with pytest.raises(export.ExportUnknown):
        session.download(PATH, 1024)
    assert len(engine.requests) == before and engine.events == [("pause", SID)]


def test_leaf_size_limit_refuses_before_archive_payload(monkeypatch):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    engine.stat_changes[PATH] = {"size": 1025}
    with pytest.raises(ValueError):
        session.download(PATH, 1024)
    assert not any(method == "GET" and route.endswith("/archive") for method, route, _ in engine.requests)
    assert engine.events.count(("pause", SID)) == engine.events.count(("resume", SID)) == 1


@pytest.mark.parametrize("owned", [False, True])
def test_original_finalize_persists_unknown_and_only_cleans_owned_resource(monkeypatch, tmp_path, owned):
    p, probe, options = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    session.owned = owned
    if owned:
        def lost_kill():
            engine.events.append(("kill_unknown", SID))
            raise TimeoutError("Q inert owned kill acknowledgement lost")
        monkeypatch.setattr(session.sandbox, "kill", lost_kill)
    else:
        with pytest.raises(PermissionError):
            session.download(PATH, 1024)
        assert engine.events == []
    isolation = GeneratedExperimentExecutor(adapter.LocalCpuSandboxBackend(**options)).prepare(
        p, {"candidate.py": CODE}).isolation
    root = tmp_path / context().run_id
    root.mkdir()
    _write_json(root / "plan.json", p.model_dump(mode="json"))
    result = GeneratedResult(plan=p, context=context(), archive_path=str(root), provenance="mock",
        isolation=isolation, sandbox_id=SID, execution_state="unknown", remote_effect="unknown",
        cleanup_state="unknown" if owned else "not_created")
    persisted = finalize_session(result, root, [], session)
    restored = read_generated_result(tmp_path, context().run_id, expected_plan=p, expected_context=context())
    assert restored.remote_effect == persisted.remote_effect == "unknown"
    assert restored.cleanup_state == ("unknown" if owned else "not_created")
    assert restored.assessment.hypothesis == "not_evaluated" and not restored.assessment.trusted
    assert restored.assessment.contribution == "proposed"
    assert engine.events.count(("kill_unknown", SID)) == int(owned)
    assert ("sdk_close", SID) in engine.events and ("transport_close", SID) in engine.events


@pytest.mark.parametrize("change", ["image", "resources", "host_pid", "export_mount", "third_writer", "bind_volume"])
def test_changed_effective_isolation_or_shared_writer_refuses_export(monkeypatch, change):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    if change == "image":
        engine.main["Config"]["Image"] = "mutable:1"
    elif change == "resources":
        engine.main["HostConfig"]["PidsLimit"] *= 2
    elif change == "host_pid":
        engine.main["HostConfig"]["PidMode"] = "host"
    elif change == "export_mount":
        engine.main["Mounts"].append({"Type": "bind", "Destination": "/tmp", "RW": True})
    elif change == "third_writer":
        engine.users.append({"Id": "4" * 64})
    else:
        engine.volume["Options"] = {"type": "none", "o": "bind", "device": "/host"}
    with pytest.raises(PermissionError):
        session.download(PATH, 1024)
    assert not any(route.endswith("/archive") for _, route, _ in engine.requests)
    assert engine.events == []


@pytest.mark.parametrize("path", ["/tmp", "/tmp/morph-research/nested", PATH])
def test_symlink_ancestor_or_leaf_refuses_archive_and_restores_same_session(monkeypatch, path):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    engine.stat_changes[path] = {"mode": (1 << 27) | 0o777, "linkTarget": "/outside"}
    with pytest.raises(PermissionError):
        session.download(PATH, 1024)
    assert not any(method == "GET" and route.endswith("/archive") for method, route, _ in engine.requests)
    assert engine.events.count(("pause", SID)) == engine.events.count(("resume", SID)) == 1
    assert all(reply.closed for reply in engine.replies)


@pytest.mark.parametrize("attack", ["link", "fifo", "extra", "path", "pax", "compressed", "truncated", "oversized"])
def test_invalid_or_unbounded_archive_is_rejected_without_host_extraction(monkeypatch, attack):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    if attack == "link":
        engine.archive = archive_bytes(kind=tarfile.LNKTYPE)
    elif attack == "fifo":
        engine.archive = archive_bytes(kind=tarfile.FIFOTYPE)
    elif attack == "extra":
        engine.archive = archive_bytes(extra=True)
    elif attack == "path":
        engine.archive = archive_bytes(name="../result.bin")
    elif attack == "pax":
        engine.archive = archive_bytes(pax={"path": "result.bin"})
    elif attack == "compressed":
        engine.encoding = "gzip"
    elif attack == "truncated":
        engine.archive = engine.archive[:1024]
    else:
        engine.archive = b"x" * (1024 + 65537)
    def denied(*args, **kwargs):
        raise AssertionError("Q forbids host tar extraction")
    monkeypatch.setattr(tarfile.TarFile, "extract", denied)
    monkeypatch.setattr(tarfile.TarFile, "extractall", denied)
    with pytest.raises((ValueError, PermissionError, tarfile.TarError)):
        session.download(PATH, 1024)
    assert session.export_control.observations == []
    assert engine.events.count(("pause", SID)) == engine.events.count(("resume", SID)) == 1
    assert all(reply.closed for reply in engine.replies)


@pytest.mark.parametrize("applied", [False, True])
def test_pause_timeout_keeps_unknown_without_redelivery_even_after_read_only_recovery(monkeypatch, applied):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration)
    session.sandbox.apply_pause = applied
    session.sandbox.pause_failure = TimeoutError("Q inert pause acknowledgement lost")
    with pytest.raises(export.ExportUnknown):
        session.download(PATH, 1024)
    assert engine.events.count(("pause", SID)) == 1
    assert engine.events.count(("resume", SID)) == int(applied)
    assert not any(route.endswith("/archive") for _, route, _ in engine.requests)
    before = deepcopy(engine.events), len(engine.requests)
    for action in [lambda: session.download(PATH, 1024), lambda: session.upload(PATH, b"x"),
                   lambda: session.run(["python3", "candidate.py"], 1, "/tmp/morph-research")]:
        with pytest.raises(export.ExportUnknown):
            action()
    assert (engine.events, len(engine.requests)) == before
    session.destroy()
    session.close()
    assert [event for event in engine.events if event[0] == "kill"] == [("kill", SID)]


@pytest.mark.parametrize("effect", ["resume_timeout", "foreign_resume", "stream_disconnect", "late_read", "metadata_changed"])
def test_unknown_read_or_restore_prevents_later_work_and_cleans_only_owned_session(monkeypatch, effect):
    _, probe, _ = configured()
    session, engine = owned_session(monkeypatch, probe.configuration,
        resume_failure=TimeoutError("Q inert resume acknowledgement lost") if effect == "resume_timeout" else None,
        resumed_id="q-foreign-connection" if effect == "foreign_resume" else SID)
    if effect == "stream_disconnect":
        engine.stream_failure = ConnectionResetError("Q inert archive stream disconnected")
    elif effect == "late_read":
        clock = SimpleNamespace(now=0.0)
        monkeypatch.setattr(export, "time", SimpleNamespace(monotonic=lambda: clock.now))
        engine.read_hook = lambda: setattr(clock, "now", 11.0)
    elif effect == "metadata_changed":
        engine.get_stat_changes = {"mtime": "2026-10-03T00:00:01Z"}
    with pytest.raises(export.ExportUnknown):
        session.download(PATH, 1024)
    before = deepcopy(engine.events), len(engine.requests)
    with pytest.raises(export.ExportUnknown):
        session.download(PATH, 1024)
    assert (engine.events, len(engine.requests)) == before
    assert engine.events.count(("pause", SID)) == engine.events.count(("resume", SID)) == 1
    assert all(reply.closed for reply in engine.replies)
    session.destroy()
    session.close()
    assert [event for event in engine.events if event[0] == "kill"] == [("kill", SID)]
    if effect == "foreign_resume":
        assert ("sdk_close", "q-foreign-connection") in engine.events


def test_official_create_timeout_is_durable_unknown_and_same_run_is_not_recreated(monkeypatch, tmp_path):
    p, probe, options = configured()
    engine = install_engine(monkeypatch, probe.configuration)
    calls = []
    def lost_create(*args, **kw):
        calls.append((args, kw))
        raise TimeoutError("Q inert create acknowledgement lost")
    monkeypatch.setattr(adapter.SandboxSync, "create", lost_create)
    backend = adapter.LocalCpuSandboxBackend(**options)
    executor = GeneratedExperimentExecutor(backend, probe_registry=TrustedProbeRegistry(records=(probe,)))
    result = executor.execute(p, context(), {"candidate.py": CODE}, tmp_path)
    assert result.execution_state == result.remote_effect == result.cleanup_state == "unknown"
    assert len(calls) == 1 and engine.events == [("transport_close", SID)]
    restored = read_generated_result(tmp_path, context().run_id, expected_plan=p, expected_context=context())
    assert restored.assessment.execution == "unknown" and restored.assessment.hypothesis == "not_evaluated"
    assert restored.assessment.contribution == "proposed" and not restored.assessment.trusted
    assert json.loads((tmp_path / context().run_id / "result.json").read_bytes())["sandbox_id"] is None
    with pytest.raises(FileExistsError):
        executor.execute(p, context(), {"candidate.py": CODE}, tmp_path)
    assert len(calls) == 1
