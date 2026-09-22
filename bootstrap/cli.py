import argparse
from pathlib import Path

from bootstrap.sample import prepare_workspace
from bootstrap.verify import SampleVerifier
from contracts.identity import AgentId


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or independently verify the fixed exercise")
    parser.add_argument("action", choices=["prepare", "verify"])
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        print(prepare_workspace(args.workspace))
        return 0
    evidence = args.evidence_dir or args.workspace.resolve().with_name(
        args.workspace.name + "-evidence"
    )
    verdict = SampleVerifier(evidence).verify(
        str(args.workspace), AgentId(role="reviewer", instance=0)
    )
    print(verdict.model_dump_json(indent=2))
    return 0 if verdict.passed else 1
