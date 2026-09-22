"""Safe, bounded adapters for the dashboard's documented input formats.

Runtime data is accepted only from a small local allowlist and is represented as
plain JSON suitable for the static dashboard.  This module deliberately does
not turn arbitrary JSON or a mock fixture into task-live evidence.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from contracts.messages import Envelope
from contracts.resolution import Gene
from contracts.results import TaskResult
from metabolism import GeneView, UseRecord
from orchestration.rehearsal import read_rehearsal
from orchestration.rehearsal_models import RehearsalDocument

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
    adoptions: list[dict[str, Any]]
    metrics: list[dict[str, Any]]
    result: dict[str, Any] | None
    hub_status: str
    source_label: str
    notes: list[str]
    rehearsal: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provenance": self.provenance,
            "acceptance": self.acceptance,
            "events": self.events,
            "genes": self.genes,
            "adoptions": self.adoptions,
            "metrics": self.metrics,
            "result": self.result,
            "hub_status": self.hub_status,
            "source_label": self.source_label,
            "notes": self.notes,
            "rehearsal": self.rehearsal,
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
        adoptions=[],
        metrics=[],
        result=None,
        hub_status="待发布（未配置 Hub 沙箱）",
        source_label="未加载导出",
        notes=[note],
    )


def load_rehearsal(path: Path, *, replay: bool = False) -> DashboardData:
    """Load R's one typed, local fixed-rehearsal snapshot without adapting it."""
    resolved = path.resolve()
    if resolved.name != "rehearsal.json" or resolved.suffix.lower() != ".json":
        raise DashboardInputError("彩排输入必须是 R 输出的 rehearsal.json")
    if not resolved.is_file():
        raise DashboardInputError("彩排快照不存在")
    if resolved.stat().st_size > MAX_INPUT_BYTES:
        raise DashboardInputError("彩排快照超过 2 MiB 限制")
    try:
        # R owns the replay downgrade: V never rewrites a TaskResult merely to
        # make an old history look like a live run.
        document: RehearsalDocument = read_rehearsal(resolved, replay=replay)
    except Exception as error:
        raise DashboardInputError(f"彩排快照不符合 R 的共享类型: {error}") from error

    current = document.current
    mode_label = {"live": "现场快照", "replay": "回放视图", "mock": "模拟快照"}[document.mode]
    return DashboardData(
        provenance=document.mode,
        acceptance=current.acceptance.model_dump(mode="json"),
        events=[],
        genes=[gene.model_dump(mode="json") for gene in current.genes],
        adoptions=[adoption.model_dump(mode="json") for adoption in current.adoptions],
        metrics=[],
        result=current.results[-1].model_dump(mode="json") if current.results else None,
        hub_status="待发布（未配置 Hub 沙箱）",
        source_label=f"固定彩排 rehearsal.json（{mode_label}）",
        notes=[
            f"{mode_label}：第 {current.sequence} 个快照。",
            "成员移除只发生在两项任务之间；不表示终止在途模型进程后恢复。",
            "费用为未知时保留未知，不显示为零。",
        ],
        rehearsal=document.model_dump(mode="json"),
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
        return cast(dict[str, Any], Envelope.model_validate(item).model_dump(mode="json"))
    except Exception as error:
        raise DashboardInputError(f"Envelope 不符合 T0 共享契约: {error}") from error


def _validate_gene(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise DashboardInputError("Gene 必须是对象")
    try:
        return cast(dict[str, Any], Gene.model_validate(item).model_dump(mode="json"))
    except Exception as error:
        raise DashboardInputError(f"Gene 不符合共享契约: {error}") from error


def _validate_metric(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict) or not isinstance(item.get("name"), str):
        raise DashboardInputError("指标必须具有 name")
    history = item.get("history", [])
    if not isinstance(history, list) or not all(isinstance(value, (int, float)) for value in history):
        raise DashboardInputError("指标 history 必须为数值列表")
    return {"name": item["name"], "history": history, "unit": str(item.get("unit", ""))}


def _model_list(value: Any, model: type[GeneView] | type[UseRecord], label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DashboardInputError(f"{label} 必须为数组")
    try:
        return [model.model_validate(item).model_dump(mode="json") for item in value]
    except Exception as error:
        raise DashboardInputError(f"{label} 不符合共享只读模型: {error}") from error


def _from_document(document: Any, source_label: str) -> DashboardData:
    if not isinstance(document, dict):
        raise DashboardInputError("JSON 文档必须为对象")
    provenance = str(document.get("provenance", "mock"))
    if provenance not in PROVENANCE_VALUES:
        raise DashboardInputError("provenance 必须为 live、replay 或 mock")
    if provenance != "mock":
        raise DashboardInputError("JSON 文档入口仅用于显式 mock fixture；真实来源必须使用 T2 JSONL Envelope 导出")
    events = [_validate_envelope(item) for item in document.get("events", [])]
    genes = [_validate_gene(item) for item in document.get("genes", [])]
    metrics = [_validate_metric(item) for item in document.get("metrics", [])]
    if not all(event["provenance"] == provenance for event in events):
        raise DashboardInputError("文档和事件的 provenance 必须一致")
    if not all(gene["provenance"] == provenance for gene in genes):
        raise DashboardInputError("文档和 Gene 的 provenance 必须一致")
    return DashboardData(
        provenance=provenance,
        acceptance=_acceptance(document.get("acceptance"), provenance),
        events=events,
        genes=genes,
        adoptions=[],
        metrics=metrics,
        result=None,
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
            adoptions=[],
            metrics=[],
            result=None,
            hub_status="待发布（未配置 Hub 沙箱）",
            source_label=f"T2 JSONL 事件导出：{safe_path.name}",
            notes=["该导出只含 Envelope；未导出 Gene 正文与历史指标，相关视图保持空态。"],
        )
    return _from_document(json.loads(text), f"mock fixture：{safe_path.name}")


def _safe_runtime_root(path: Path, project_root: Path) -> Path:
    """Accept only a named T2 evidence root or a project-local exported run."""
    resolved = path.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    project_exports = (project_root / "runtime_exports").resolve()
    is_project_export = resolved.is_relative_to(project_exports)
    is_t2_temp_export = resolved.parent == temp_root and resolved.name.startswith("morph-t2-")
    if path.is_symlink() or not resolved.is_dir() or not (is_project_export or is_t2_temp_export):
        raise DashboardInputError("运行目录必须是受限的 runtime_exports 子目录或 T2 命名临时证据目录")
    return resolved


def _read_runtime_json(path: Path, label: str) -> Any:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_INPUT_BYTES:
        raise DashboardInputError(f"{label} 缺失、不是普通文件或超过 2 MiB")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DashboardInputError(f"{label} 不是有效 JSON") from error


def load_runtime_export(root: Path, project_root: Path) -> DashboardData:
    """Load T2's fixed evidence sidecars without inferring data from payloads.

    Required files are `events.jsonl` (T2 `Envelope` export) and `result.json`
    (`TaskResult`). Optional `genes.json` and `adoption.json` are T3M's exact
    `GeneView` and `UseRecord` snapshots. No payload scraping or fallback
    promotion of acceptance occurs here.
    """
    safe_root = _safe_runtime_root(root, project_root)
    events_path = safe_root / "events.jsonl"
    if not events_path.is_file() or events_path.is_symlink() or events_path.stat().st_size > MAX_INPUT_BYTES:
        raise DashboardInputError("events.jsonl 缺失、不是普通文件或超过 2 MiB")
    events = [_validate_envelope(json.loads(line)) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = TaskResult.model_validate(_read_runtime_json(safe_root / "result.json", "result.json"))
    if events and any(event["run_id"] != result.run_id or event["provenance"] != result.provenance for event in events):
        raise DashboardInputError("events.jsonl 与 result.json 的 run_id/provenance 不一致")
    genes_path = safe_root / "genes.json"
    adoptions_path = safe_root / "adoption.json"
    genes = _model_list(_read_runtime_json(genes_path, "genes.json"), GeneView, "genes.json") if genes_path.exists() else []
    adoptions = _model_list(_read_runtime_json(adoptions_path, "adoption.json"), UseRecord, "adoption.json") if adoptions_path.exists() else []
    if any(item["run_id"] != result.run_id or item["provenance"] != result.provenance for item in adoptions):
        raise DashboardInputError("adoption.json 与 result.json 的 run_id/provenance 不一致")
    if any(item["provenance"] != result.provenance for item in genes):
        raise DashboardInputError("genes.json 与 result.json 的 provenance 不一致")
    notes = ["T2 运行证据：Envelope、TaskResult 与可选 T3M GeneView/UseRecord 均按共享模型重验。"]
    if not genes:
        notes.append("未提供 genes.json 或快照为空；Gene 谱系保持空态。")
    if not adoptions:
        notes.append("未提供 adoption.json 或本次未采用 Gene；不从注入或候选推断采用。")
    return DashboardData(
        provenance=result.provenance,
        acceptance=result.acceptance.model_dump(mode="json"),
        events=events,
        genes=genes,
        adoptions=adoptions,
        metrics=[],
        result=result.model_dump(mode="json"),
        hub_status="待发布（未配置 Hub 沙箱）",
        source_label=f"T2 受限运行证据：{safe_root.name}",
        notes=notes,
    )
