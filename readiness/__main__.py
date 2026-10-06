"""``python -m readiness`` — print one readiness report, or the example manifest.

Read-only and bounded: it declares no probes of its own beyond what the
environment and the manifest provide, and it never retries a probe.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from contracts.readiness import SUBJECTS
from readiness.catalog import ReadinessConfigError, build_service, example_manifest_json

_STATES = ("not_run", "ok", "degraded", "blocked", "failed")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="readiness",
        description="输出本机、接口与账号三维健全度快照；未声明的维度保持未探测。",
    )
    parser.add_argument("--manifest", type=Path, help="接入清单 JSON（cli/mcp/credential 探针声明）")
    parser.add_argument("--no-local", action="store_true", help="不加入本机探针")
    parser.add_argument("--cache-seconds", type=float, default=0.0, help="报告缓存秒数（默认 0，一次性执行）")
    parser.add_argument("--budget-seconds", type=float, help="本次报告的总时间预算")
    parser.add_argument(
        "--fail-on",
        default="failed,blocked",
        help="总体状态命中这些值即返回退出码 1（逗号分隔；默认 failed,blocked）",
    )
    parser.add_argument("--example-manifest", action="store_true", help="打印参考接入清单后退出")
    args = parser.parse_args()

    if args.example_manifest:
        print(example_manifest_json())
        return 0

    thresholds = [entry.strip() for entry in args.fail_on.split(",") if entry.strip()]
    invalid = [entry for entry in thresholds if entry not in _STATES]
    if invalid:
        parser.error(f"--fail-on 只接受 {'/'.join(_STATES)}，收到：{', '.join(invalid)}")

    try:
        service = build_service(
            manifest=args.manifest,
            local=not args.no_local,
            cache_seconds=args.cache_seconds,
            budget_seconds=args.budget_seconds,
        )
    except ReadinessConfigError as error:
        print(f"接入清单未通过校验，未执行任何探针：{error}", file=sys.stderr)
        return 2

    report = service.report()
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    dimensions = " ".join(f"{subject}={report.dimensions[subject]}" for subject in SUBJECTS)
    print(f"overall={report.overall} {dimensions}", file=sys.stderr)
    return 1 if report.overall in thresholds else 0


if __name__ == "__main__":
    raise SystemExit(main())
