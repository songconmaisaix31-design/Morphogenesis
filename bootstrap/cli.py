"""Unified Morphogenesis usage entry point.

One command, several subcommands: the fixed exercise (prepare/verify), the live
execution loop (acceptance), the fixed two-task rehearsal, the read-only local
dashboard (serve), a local quality gate (check), and a placeholder for the
not-yet-merged decentralized swarm.

Subcommands that wrap an existing ``python -m <module>`` entry forward the
remaining arguments unchanged to that module in the same interpreter, so each
module's own argparse help, exit codes, blocking ``serve_forever`` and signal
handling stay identical to the documented ``python -m ...`` invocations.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts.identity import AgentId

Handler = Callable[[argparse.Namespace], int]

#: ``subcommand -> module`` for entries forwarded verbatim to ``python -m ...``.
_FORWARD = {
    "acceptance": "orchestration.acceptance",
    "rehearsal": "orchestration.rehearsal",
    "serve": "viz.server",
}


def _forward(module: str, argv: list[str]) -> int:
    return subprocess.call([sys.executable, "-m", module, *argv])


def _prepare(args: argparse.Namespace) -> int:
    print(prepare_workspace(args.workspace))
    return 0


def _verify(args: argparse.Namespace) -> int:
    evidence = args.evidence_dir or args.workspace.resolve().with_name(
        args.workspace.name + "-evidence"
    )
    verdict = SampleVerifier(evidence).verify(
        str(args.workspace), AgentId(role="reviewer", instance=0)
    )
    print(verdict.model_dump_json(indent=2))
    return 0 if verdict.passed else 1


def _check(args: argparse.Namespace) -> int:
    """Run the local Python quality gate: full test suite then strict mypy.

    Build, SDK and installed-wheel checks remain separate heavier steps (they
    need npm ci / a built wheel) and are documented in README and CI.
    """
    root = Path(__file__).resolve().parent.parent
    steps = [
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, str(root / "tools" / "typecheck.py")],
    ]
    for command in steps:
        code = subprocess.call(command, cwd=root)
        if code != 0:
            return code
    return 0


def _swarm(args: argparse.Namespace) -> int:
    print(
        "swarm 子命令尚未合入主线：异构蜂群与 /api/swarm 仍位于 decentralized-swarm 分支，"
        "主线仅保留展示占位。",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    # Forwarded subcommands bypass argparse so the target module's own --help,
    # argument errors and exit codes pass through verbatim.
    if len(sys.argv) > 1 and sys.argv[1] in _FORWARD:
        return _forward(_FORWARD[sys.argv[1]], sys.argv[2:])

    parser = argparse.ArgumentParser(
        prog="morphogenesis",
        description="Morphogenesis 固定规模蜂群原型：统一使用入口。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="生成固定练习 workspace（不执行模型）")
    prepare.add_argument("--workspace", type=Path, required=True)
    prepare.set_defaults(func=_prepare)

    verify = sub.add_parser("verify", help="独立固定验证器复核 workspace")
    verify.add_argument("--workspace", type=Path, required=True)
    verify.add_argument("--evidence-dir", type=Path)
    verify.set_defaults(func=_verify)

    acceptance = sub.add_parser(
        "acceptance", help="单次真实模型运行闭环（转发 python -m orchestration.acceptance）"
    )
    acceptance.set_defaults(func=lambda a: _forward("orchestration.acceptance", []))

    rehearsal = sub.add_parser(
        "rehearsal", help="两项已授权新任务固定彩排（转发 python -m orchestration.rehearsal）"
    )
    rehearsal.set_defaults(func=lambda a: _forward("orchestration.rehearsal", []))

    serve = sub.add_parser("serve", help="只读本地 dashboard（转发 python -m viz.server）")
    serve.set_defaults(func=lambda a: _forward("viz.server", []))

    check = sub.add_parser("check", help="本地质量门：全量测试 + strict mypy")
    check.set_defaults(func=_check)

    swarm = sub.add_parser("swarm", help="异构去中心化蜂群（占位，尚未合入主线）")
    swarm.set_defaults(func=_swarm)

    args = parser.parse_args()
    handler: Handler = args.func
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
