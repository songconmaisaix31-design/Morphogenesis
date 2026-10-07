"""Thin reuse of the fixed pure-function gate and independent sample tests.

This is not an OS sandbox or a general Python runner. Only the existing
three-function language is admitted, in a credential-free isolated interpreter.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from bootstrap import acceptance_runner
from bridge_node.environment import child_environment
from local_assets.models import AssetSafetyError, Candidate, CommandResult, SampleValidationPolicy
from local_assets.paths import relative_path
from orchestration.sample_policy import validate_sample


def inspect_sample(candidate: Candidate, policy: SampleValidationPolicy) -> str:
    path = relative_path(policy.path)
    if Path(path).name != "sample.py" or len(candidate.changes) != 1:
        raise AssetSafetyError("fixed_sample_path_required")
    change = candidate.changes[0]
    if change.path != path or change.after is None or change.before is None:
        raise AssetSafetyError("fixed_sample_patch_required")
    if len(change.after.encode("utf-8")) > 16384:
        raise AssetSafetyError("fixed_sample_size_limit")
    try:
        validate_sample(change.after)
    except (SyntaxError, ValueError, RecursionError):
        raise AssetSafetyError("fixed_sample_allowlist_rejected") from None
    return change.after


def validate_fixed_sample(source: str, policy: SampleValidationPolicy, timeout: float) -> CommandResult:
    # Tests and dependencies come from the installed host, never the task tree.
    # The caller already checked this exact source with inspect_sample.
    runner = Path(acceptance_runner.__file__).resolve()
    interpreter = str(Path(sys.base_prefix) / "python.exe") if os.name == "nt" else sys.executable
    with tempfile.TemporaryDirectory(prefix="swarm-fixed-review-") as temporary:
        root = Path(temporary)
        snapshot = root / "candidate.py"
        snapshot.write_bytes(source.encode("utf-8"))
        completed = subprocess.run(
            [interpreter, "-I", "-S", str(runner), str(snapshot)], cwd=root,
            env=child_environment(root), capture_output=True, timeout=timeout,
            check=False, shell=False,
        )
        if len(completed.stdout) + len(completed.stderr) > 128 * 1024:
            raise AssetSafetyError("fixed_sample_output_limit")
        records = [line.removeprefix(b"MORPH_CHECKPOINTS=")
                   for line in completed.stdout.splitlines() if line.startswith(b"MORPH_CHECKPOINTS=")]
        expected = {"tests_run": 3, "checks": {"clamp": True, "mean": True, "unique": True}}
        if (completed.returncode != 0 or len(records) != 1 or json.loads(records[0]) != expected
                or snapshot.read_bytes() != source.encode("utf-8")):
            raise AssetSafetyError("fixed_sample_acceptance_failed")
    return CommandResult(argv=(policy.executor, policy.version), exit_code=0)
