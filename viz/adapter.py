"""Safe, bounded adapters for the dashboard's documented input formats.

Runtime data is accepted only from a small local allowlist and is represented as
plain JSON suitable for the static dashboard.  This module deliberately does
not turn arbitrary JSON or a mock fixture into task-live evidence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from contracts.messages import Envelope

MAX_INPUT_BYTES = 2 * 1024 * 1024
ALLOWED_SUFFIXES = {".json", ".jsonl"}
ACCEPTANCE_STATES = {"not_run", "passed", "failed", "blocked"}
PROVENANCE_VALUES = {"live", "replay", "mock"}


class DashboardInputError(ValueError):
    """Raised when a local export is outside the dashboard's input contract."""


@dataclass(frozen=True)
class DashboardData:
    provenance: str
    acceptance: dict[str, str]
    events: list[dict[str, Any]]
    genes: list[dict[str, Any]]
    metrics: list[dict[str, Any]]
    hub_status: str
    source_label: str
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "provenance": self.provenance,
            "acceptance": self.acceptance,
            "events": self.events,
            "genes": self.genes,
            "metrics": self.metrics,
            "hub_status": self.hub_status,
            "source_label": self.source_label,
            "notes": self.notes,
        }


def empty_dashboard(note: str = "尚未加载运行事件导出。") -> DashboardData:
    return DashboardData(
        provenance="live",
        acceptance={
            "contract_local": "not_run",
            "interface_live": "not_run",
            "task_live": "not_run",
        },
        events=[],
        genes=[],
        metrics=[],
        hub_status="待发布（未配置 Hub 沙箱）",
        source_label="未加载导出",
        notes=[note],
    )


def _safe_path(path: Path, roots: tuple[Path, ...]) -> Path:
    resolved = path.resolve()
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise DashboardInputError("仅允许 .json 或 .jsonl 输入")
    if not any(resolved.is_relative_to(root.resolve()) for root in roots):
        raise DashboardInputError("输入文件必须位于 demo/data 或 runtime_exports")
    if not resolved.is_file():
        raise DashboardInputError("输入文件不存在")
    if resolved.stat().st_size > MAX_INPUT_BYTES:
        raise DashboardInputError("输入文件超过 2 MiB 限制")
    return resolved


def _acceptance(value: Any, provenance: str) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    result = {key: str(source.get(key, "not_run")) for key in (
        "contract_local", "interface_live", "task_live"
    )}
    if any(state not in ACCEPTANCE_STATES for state in result.values()):
        raise DashboardInputError("验收状态不在共享契约允许范围内")
    if provenance != "live" and (
        result["interface_live"] == "passed" or result["task_live"] == "passed"
    ):
        raise DashboardInputError("mock/replay 不得标记任何 live 验收为 passed")
    return result


def _validate_envelope(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise DashboardInputError("JSONL 的每行必须是 Envelope 对象")
    try:
        # T2 serializes this exact shared model. Revalidate instead of keeping a
        # local approximation of identities, seq, lineage, or provenance rules.
        return Envelope.model_validate(item).model_dump(mode="json")
    except Exception as error:
        raise DashboardInputError(f"Envelope 不符合 T0 共享契约: {error}") from error


def _validate_gene(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict) or not isinstance(item.get("ref"), dict):
        raise DashboardInputError("Gene 必须包含 ref 对象")
    ref = item["ref"]
    if not isinstance(ref.get("gene_id"), str) or not ref["gene_id"]:
        raise DashboardInputError("Gene.ref.gene_id 必须为非空字符串")
    if not isinstance(item.get("strategy"), list) or not item["strategy"]:
        raise DashboardInputError("Gene.strategy 必须为非空列表")
    if item.get("provenance", "live") not in PROVENANCE_VALUES:
        raise DashboardInputError("Gene.provenance 无效")
    return item


def _validate_metric(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict) or not isinstance(item.get("name"), str):
        raise DashboardInputError("指标必须具有 name")
    history = item.get("history", [])
    if not isinstance(history, list) or not all(isinstance(value, (int, float)) for value in history):
        raise DashboardInputError("指标 history 必须为数值列表")
    return {"name": item["name"], "history": history, "unit": str(item.get("unit", ""))}


def _from_document(document: Any, source_label: str) -> DashboardData:
    if not isinstance(document, dict):
        raise DashboardInputError("JSON 文档必须为对象")
    provenance = str(document.get("provenance", "mock"))
    if provenance not in PROVENANCE_VALUES:
        raise DashboardInputError("provenance 必须为 live、replay 或 mock")
    events = [_validate_envelope(item) for item in document.get("events", [])]
    genes = [_validate_gene(item) for item in document.get("genes", [])]
    metrics = [_validate_metric(item) for item in document.get("metrics", [])]
    if not all(event["provenance"] == provenance for event in events):
        raise DashboardInputError("文档和事件的 provenance 必须一致")
    return DashboardData(
        provenance=provenance,
        acceptance=_acceptance(document.get("acceptance"), provenance),
        events=events,
        genes=genes,
        metrics=metrics,
        hub_status="待发布（未配置 Hub 沙箱）",
        source_label=source_label,
        notes=[str(note) for note in document.get("notes", []) if isinstance(note, str)],
    )


def load_dashboard(path: Path, project_root: Path) -> DashboardData:
    """Load an allowlisted mock document or T2's JSONL Envelope export.

    JSONL is T2's runtime handoff: it has message flow but no invented Gene or
    metric semantics.  The JSON document form is reserved for labelled mock
    fixtures and tests, where genes and metrics are explicitly supplied.
    """
    safe_path = _safe_path(path, (project_root / "demo" / "data", project_root / "runtime_exports"))
    text = safe_path.read_text(encoding="utf-8")
    if safe_path.suffix.lower() == ".jsonl":
        events = [_validate_envelope(json.loads(line)) for line in text.splitlines() if line.strip()]
        provenance = events[0]["provenance"] if events else "live"
        if any(event["provenance"] != provenance for event in events):
            raise DashboardInputError("单个 JSONL 导出不得混合 provenance")
        return DashboardData(
            provenance=provenance,
            acceptance=_acceptance({}, provenance),
            events=events,
            genes=[],
            metrics=[],
            hub_status="待发布（未配置 Hub 沙箱）",
            source_label=f"T2 JSONL 事件导出：{safe_path.name}",
            notes=["该导出只含 Envelope；未导出 Gene 正文与历史指标，相关视图保持空态。"],
        )
    return _from_document(json.loads(text), f"mock fixture：{safe_path.name}")
