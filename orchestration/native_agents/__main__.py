"""Safe discovery by default; model launches require an explicit execute flag."""

import argparse
import json
from pathlib import Path
import sys

from orchestration.native_agents.launch import build_launch, write_mcp_config
from orchestration.native_agents.models import LaunchRequest
from orchestration.native_agents.process import launch_interactive, run_headless
from orchestration.native_agents.registry import REGISTRY, probe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("probe", help="version/auth only, no model call")
    sub.add_parser("matrix", help="supported contracts, distinct from actual validation")
    launch = sub.add_parser("launch")
    launch.add_argument("--request", type=Path, required=True, help="trusted LaunchRequest JSON")
    launch.add_argument("--evidence", type=Path, required=True)
    launch.add_argument("--timeout", type=float, default=120)
    launch.add_argument("--max-tool-calls", type=int, default=12)
    launch.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.action == "probe":
        results = [probe(runtime) for runtime in REGISTRY]
        print(json.dumps([result.model_dump(mode="json") for result in results], ensure_ascii=False, indent=2))
        return 0 if all(result.authenticated is True and result.version_matches is True for result in results) else 1
    if args.action == "matrix":
        print(json.dumps({key: spec.model_dump(mode="json") for key, spec in REGISTRY.items()}, indent=2))
        return 0
    request = LaunchRequest.model_validate_json(args.request.read_text(encoding="utf-8"))
    evidence = args.evidence.resolve()
    mcp_path = evidence.with_name(evidence.name + ".mcp.json")
    plan = build_launch(request, claude_mcp_path=mcp_path)
    if not args.execute:
        print(plan.model_dump_json(indent=2))
        return 0
    preflight = probe(request.runtime)
    if preflight.authenticated is not True or preflight.version_matches is not True:
        raise ValueError("native version/auth preflight did not pass; no model invocation")
    if args.timeout <= 0 or args.max_tool_calls <= 0:
        raise ValueError("positive invocation limits are required")
    if request.mode == "headless" and evidence.exists():
        raise FileExistsError("existing evidence directory cannot be replayed")
    if request.mode == "interactive" and (not sys.stdin.isatty() or not sys.stdout.isatty()):
        raise ValueError("interactive launch requires a caller-owned terminal")
    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    write_mcp_config(plan, mcp_path)
    if request.mode == "interactive":
        owner = launch_interactive(plan)
        try:
            import time
            started = time.monotonic()
            while owner.poll() is None:
                if time.monotonic() - started >= args.timeout:
                    owner.cancel()
                    return 1
                time.sleep(0.1)
        except KeyboardInterrupt:
            owner.cancel()
            return 1
        finally:
            owner.cancel()
        return owner.poll() or 0
    outcome = run_headless(plan, evidence, timeout_seconds=args.timeout, max_tool_calls=args.max_tool_calls)
    print(outcome.model_dump_json(indent=2))
    return 0 if outcome.state == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
