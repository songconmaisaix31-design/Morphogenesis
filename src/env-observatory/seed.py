"""Seed a demo research project so the environment observatory has real data.

Idempotent: every ``create_project`` / ``create_branch`` / ``propose_work`` /
``submit_note`` deduplicates against the persisted knowledge, so re-running this
script never creates duplicate projects, branches, tasks or notes. It also
writes the resulting HostConfig JSON to ``.state/host-config.json`` so
``server.py`` can bind the same host identity through
``OBSERVATORY_HOST_CONFIG``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from contracts.identity import AgentId
from swarm.research.models import HostConfig
from swarm.research.records import SourceRef
from swarm.research.service import build_service

# OBSERVATORY_STATE_DIR lets the runtime live off a full system disk.
STATE_DIR = Path(os.environ.get("OBSERVATORY_STATE_DIR") or (Path(__file__).resolve().parent / ".state"))
HOST_CONFIG_PATH = STATE_DIR / "host-config.json"

SWARM_ID = "swarm-gen-1"
PROJECT_ID = "p1"
WORKER_ID = "w-01"
GOAL = "比较不同边界处理与采样策略，求解一维泊松方程，得到可验证、可继承的数值方法"

# (branch_id, title, goal)
BRANCHES = [
    ("b-soft", "软边界方法", "探索软边界条件下一维泊松方程的数值处理"),
    ("b-sampling", "自适应采样", "探索自适应采样策略对收敛与误差的影响"),
    ("b-hard", "硬边界方法", "探索硬边界嵌入的数值验证方案"),
    ("b-cross", "跨域链接", "软硬边界与采样策略的交叉验证"),
]

# (kind, goal, justification, expected_contribution, branch_id, required_capability)
PROPOSALS = [
    ("question", "文献调研：软边界与硬边界的处理方法", "需要先明确两类边界的既有处理方式",
     "形成边界处理方法的调研结论", "b-soft", "research"),
    ("experiment", "实验设计：软边界对照方案", "缺少软边界的对照实验设计",
     "得到可复现的对照实验方案", "b-soft", "research"),
    ("experiment", "生成候选：软边界实验代码", "需要实现软边界的候选求解代码",
     "产出候选实验代码", "b-soft", "research"),
    ("counterexample_check", "独立复核：复现软边界结果", "软边界结果需要独立复核",
     "独立的复现结论", "b-soft", "review"),
    ("experiment", "硬边界嵌入验证", "需要验证硬边界嵌入的正确性",
     "硬边界嵌入的验证结果", "b-hard", "research"),
    ("alternative_route", "自适应采样探索", "探索自适应采样替代均匀采样",
     "自适应采样的探索结论", "b-sampling", "research"),
]

# (kind, text, branch_id, signer, source_id) — signer/source_id may be None
NOTES = [
    ("expert_opinion", "倾向软边界方法 A，但未提供独立数据", "b-soft", "Dr. Y", None),
    ("expert_opinion", "硬边界可能引入数值不稳定，建议与软边界对比", "b-hard", "Dr. Z", None),
    ("observation", "软边界在粗网格下仍能保持二阶精度", "b-soft", None, "src-soft-grid"),
    ("observation", "自适应采样在高梯度区域显著降低误差", "b-sampling", None, "src-sampling"),
]


def host_config() -> HostConfig:
    return HostConfig(
        ledger_path=str(STATE_DIR / "tasks.sqlite3"),
        swarm_id=SWARM_ID,
        workspace=str(STATE_DIR / "workspace"),
        worker_id=WORKER_ID,
        agent=AgentId(role="builder", instance=0),
        authorized_scopes=("science",),
        capabilities=("research", "review"),
        assets_root=str(STATE_DIR / "assets"),
        evidence_root=str(STATE_DIR / "evidence"),
        project_id=PROJECT_ID,
    )


def source_ref(source_id: str) -> SourceRef:
    return SourceRef(source_id=source_id, kind="text", identifier=source_id, retrieval="present")


def ensure_dirs() -> None:
    for name in ("workspace", "assets", "evidence"):
        (STATE_DIR / name).mkdir(parents=True, exist_ok=True)


def seed(service) -> None:
    service.create_project(PROJECT_ID, GOAL, allowed_domains=("numerical_pde",),
                           data_bounds={"data": "synthetic-only"})
    for branch_id, title, goal in BRANCHES:
        service.create_branch(PROJECT_ID, branch_id, title, goal)
    for kind, goal, justification, contribution, branch_id, capability in PROPOSALS:
        service.propose_work(PROJECT_ID, kind, goal, justification, contribution,
                             branch_id=branch_id, required_capability=capability)
    for kind, text, branch_id, signer, src_id in NOTES:
        refs = (source_ref(src_id),) if src_id else ()
        service.submit_note(PROJECT_ID, kind, text, branch_id=branch_id, signer=signer,
                            source_refs=refs)


def main() -> None:
    ensure_dirs()
    config = host_config()
    service = build_service(config)
    seed(service)

    HOST_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    HOST_CONFIG_PATH.write_text(config.model_dump_json(indent=2), encoding="utf-8")

    package = service.research_package(PROJECT_ID)
    tasks = package.get("tasks") or []
    notes = (package.get("context") or {}).get("notes") or []
    print(f"seed 完成：项目 {PROJECT_ID}，任务 {len(tasks)}，笔记 {len(notes)}")
    print(f"HostConfig 已写入：{HOST_CONFIG_PATH}")
    print("server.py 启动前请设置：OBSERVATORY_HOST_CONFIG=" + str(HOST_CONFIG_PATH))


if __name__ == "__main__":
    main()
