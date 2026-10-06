"""The deployed probe set is data: empty by default, manifest-driven otherwise."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from readiness import AgentMcpProbe, CredentialProbe, PublicCliProbe
from readiness.catalog import (
    ENV_MANIFEST,
    EXAMPLE_MANIFEST,
    MANIFEST_SCHEMA,
    ReadinessConfigError,
    build_service,
    example_manifest_json,
    load_manifest,
)


def write_manifest(tmp_path: Path, document: Any, name: str = "probes.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def manifest(specs: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema": MANIFEST_SCHEMA, "probes": specs}


def test_no_declaration_means_only_the_machine_is_observed() -> None:
    service = build_service(environ={})
    assert service.probe_ids == ("machine:host",)


def test_interfaces_and_accounts_stay_unprobed_by_default() -> None:
    report = build_service(environ={}).report()
    assert report.dimensions["machine"] in {"ok", "degraded"}
    assert report.dimensions["interface"] == "not_run"
    assert report.dimensions["account"] == "not_run"
    assert report.overall == "degraded"


@pytest.mark.parametrize(
    "environ",
    [
        {"MORPH_READINESS_LOCAL": "0"},
        {"MORPH_READINESS_LOCAL": "false"},
        {"MORPH_READINESS_DISABLE": "machine:host"},
    ],
)
def test_the_host_probe_can_be_switched_off(environ: dict[str, str]) -> None:
    assert build_service(environ=environ).probe_ids == ()


def test_the_reference_manifest_is_itself_valid(tmp_path: Path) -> None:
    probes = load_manifest(write_manifest(tmp_path, EXAMPLE_MANIFEST))
    assert [probe.probe_id for probe in probes] == [
        "interface:wayfinder-cli",
        "interface:wayfinder-mcp",
        "account:wayfinder",
        "account:evomap",
    ]
    assert isinstance(probes[0], PublicCliProbe)
    assert isinstance(probes[1], AgentMcpProbe)
    assert isinstance(probes[3], CredentialProbe)
    assert json.loads(example_manifest_json())["schema"] == MANIFEST_SCHEMA


def test_a_declared_manifest_adds_probes_to_the_host_probe(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, manifest([
        {"kind": "cli", "probe_id": "interface:absent", "subject": "interface", "command": "morph-absent-cli-xyz"},
        {"kind": "credential", "probe_id": "account:hub", "subject": "account", "names": ["EVOMAP_API_KEY"]},
    ]))
    service = build_service(environ={ENV_MANIFEST: str(path)})
    assert service.probe_ids == ("machine:host", "interface:absent", "account:hub")
    report = service.report()
    assert [result.probe_id for result in report.results] == list(service.probe_ids)
    assert report.results[1].state == "blocked"
    assert report.dimensions["account"] == "blocked"
    assert report.overall == "blocked"


def test_a_disabled_probe_is_not_executed_even_when_declared(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, manifest([
        {"kind": "credential", "probe_id": "account:hub", "subject": "account", "names": ["EVOMAP_API_KEY"]},
    ]))
    service = build_service(environ={ENV_MANIFEST: str(path), "MORPH_READINESS_DISABLE": "account:hub"})
    assert service.probe_ids == ("machine:host",)


@pytest.mark.parametrize(
    "document",
    [
        {"schema": "morph.readiness.manifest/2", "probes": []},
        {"schema": MANIFEST_SCHEMA, "probes": []},
        {"schema": MANIFEST_SCHEMA, "probes": [{"kind": "shell", "probe_id": "p", "command": "sh"}]},
        {"schema": MANIFEST_SCHEMA, "probes": [{"kind": "cli", "probe_id": "p", "command": "sh", "shell": True}]},
        {"schema": MANIFEST_SCHEMA, "probes": [{"kind": "cli", "probe_id": "p"}]},
        {"schema": MANIFEST_SCHEMA, "probes": [
            {"kind": "cli", "probe_id": "p", "command": "sh"},
            {"kind": "cli", "probe_id": "p", "command": "sh"},
        ]},
        {"schema": MANIFEST_SCHEMA, "probes": [{"kind": "cli", "probe_id": "p", "command": "sh", "timeout_seconds": "soon"}]},
        {"schema": MANIFEST_SCHEMA, "probes": [{"kind": "cli", "probe_id": "p", "command": "sh", "subject": "cluster"}]},
        {"schema": MANIFEST_SCHEMA, "probes": [{"kind": "cli", "probe_id": "p", "command": "sh", "env_mode": "root"}]},
    ],
)
def test_a_rejected_manifest_is_fail_closed(tmp_path: Path, document: dict[str, Any]) -> None:
    with pytest.raises(ReadinessConfigError):
        load_manifest(write_manifest(tmp_path, document))


def test_a_missing_or_non_json_manifest_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ReadinessConfigError):
        load_manifest(tmp_path / "absent.json")
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    with pytest.raises(ReadinessConfigError):
        load_manifest(broken)


def test_numeric_environment_values_are_validated() -> None:
    service = build_service(environ={"MORPH_READINESS_CACHE_SECONDS": "30", "MORPH_READINESS_BUDGET_SECONDS": "15"})
    assert (service.cache_seconds, service.budget_seconds) == (30.0, 15.0)
    with pytest.raises(ReadinessConfigError):
        build_service(environ={"MORPH_READINESS_CACHE_SECONDS": "soon"})
    with pytest.raises(ReadinessConfigError):
        build_service(environ={"MORPH_READINESS_BUDGET_SECONDS": "-5"})
