"""Host roots and project reads, using only Q-created inert files and stores."""
import os
from types import SimpleNamespace

import pytest

if not os.environ.get("R1_PRODUCT_SOURCE"):
    pytest.skip("P source not selected; host import boundary NOT_RUN", allow_module_level=True)

from morph_research import materials
from morph_research.backend import ServiceBackend, UnconnectedBackend
from morph_research.r1 import DataBoundary, R1Envelope, ResearchGoal
from morph_research.r1_store import R1Store
from morph_research.web import server
from tests.integration.r1_security.test_a_host_boundaries import seeded

SPACE = "a" * 32


def test_empty_host_roots_deny_local_material(tmp_path):
    path = tmp_path / "q-inert.txt"
    path.write_text("Q fixture only", encoding="utf-8")
    with pytest.raises((ValueError, PermissionError)):
        materials.parse_material("text", str(path))


def test_explicit_host_root_allows_inert_material(tmp_path):
    path = tmp_path / "q-inert.txt"
    path.write_text("Q fixture only", encoding="utf-8")
    result = materials.parse_material("text", str(path), allowed_dirs=(str(tmp_path),))
    assert result.retrieval == "present"
    assert result.excerpt == "Q fixture only"


def test_parent_traversal_cannot_escape_host_root(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    outside = tmp_path / "q-outside.txt"
    outside.write_text("Q outside fixture only", encoding="utf-8")
    with pytest.raises((ValueError, PermissionError)):
        materials.parse_material("text", str(root / ".." / outside.name), allowed_dirs=(str(root),))


@pytest.mark.parametrize("approved", [False, True])
def test_caller_envelope_cannot_widen_handler_host_import_roots(tmp_path, monkeypatch, approved):
    root = tmp_path / "host-approved"
    root.mkdir()
    outside = tmp_path / "caller-requested"
    outside.mkdir()
    path = outside / "q-inert.txt"
    path.write_text("Q outside fixture only", encoding="utf-8")
    reads = []
    original = materials.read_bounded

    def capture(value):
        reads.append(value)
        assert value.resolve() == path.resolve(), "Q fixture attempted an unexpected read"
        return original(value)

    monkeypatch.setattr(materials, "read_bounded", capture)
    # View formatting is independent of import authority. No HTTP server/socket
    # is constructed; the actual handler route and parser/store run in process.
    monkeypatch.setattr(server, "r1_space_view", lambda *args: {})
    with R1Store(tmp_path / "product.db") as store:
        store.create_space(SPACE, "Q", ResearchGoal(objective="host file boundary"))
        store.set_envelope(SPACE, R1Envelope(target="fixture", approved=approved,
            data=DataBoundary(allowed_directories=(str(outside),))))
        handler = object.__new__(server.Handler)
        handler.server = SimpleNamespace(r1=SimpleNamespace(store=lambda space: store),
            backend=UnconnectedBackend(), spaces=SimpleNamespace(config=SimpleNamespace(
                allowed_import_dirs=(str(root),))))
        handler.form = lambda: {"kind": "text", "identifier": str(path)}
        handler.reply = lambda *args, **kwargs: None
        try:
            handler.route_research(f"/api/research-spaces/{SPACE}/sources", write=True)
        except (ValueError, PermissionError):
            pass
        assert reads == [], "untrusted envelope directories authorized a host read"
        assert store.sources(SPACE) == []


@pytest.mark.parametrize("operation", ["three_axis", "route_opportunities"])
def test_foreign_project_is_refused_before_trusted_projection_callback(tmp_path, operation):
    core = seeded(tmp_path)
    reads = []

    def projection(project_id=None):
        reads.append(project_id)
        return [] if operation == "three_axis" else {}

    backend = ServiceBackend(core, three_axis_fn=projection, route_fn=projection)
    try:
        getattr(backend, operation)("p2")
    except (ValueError, PermissionError):
        pass
    assert reads == [], "foreign project invoked the unfiltered trusted fact callback"


def test_authorized_project_retains_read_only_projection(tmp_path):
    core = seeded(tmp_path)
    reads = []

    def projection(project_id=None):
        reads.append(project_id)
        return []

    backend = ServiceBackend(core, three_axis_fn=projection)
    assert backend.three_axis("p1") == []
    assert len(reads) == 1 and reads[0] in {None, "p1"}
    assert core.ledger.snapshot() == []


def test_connected_local_service_does_not_invent_live_provenance(tmp_path):
    core = seeded(tmp_path)
    assert core.ledger.snapshot() == []
    backend = ServiceBackend(core)
    assert backend.connected()
    assert backend.provenance() != "live", "connecting local storage invented live execution provenance"
