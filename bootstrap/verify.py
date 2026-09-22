"""Independent validation boundary; executor sandbox enforcement belongs to T2."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

from contracts.identity import AgentId
from contracts.results import Verification


class SampleVerifier:
    def __init__(self, evidence_dir: str | Path, timeout_seconds: float = 15) -> None:
        self.evidence_dir = Path(evidence_dir).resolve()
        self.timeout_seconds = timeout_seconds

    def verify(self, workspace: str, reviewer: AgentId) -> Verification:
        root = Path(workspace).resolve()
        if self.evidence_dir.is_relative_to(root):
            raise ValueError("verification evidence must be outside executor workspace")
        candidate = root / "sample.py"
        if candidate.is_symlink() or candidate.resolve().parent != root:
            raise ValueError("candidate must be a regular file inside the workspace")
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        runner = Path(__file__).with_name("acceptance_runner.py").resolve()
        if runner.is_relative_to(root):
            raise ValueError("acceptance runner must be outside executor workspace")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        report = self.evidence_dir / f"verification-{uuid4().hex}.txt"
        with TemporaryDirectory(prefix="review-", dir=self.evidence_dir) as temporary:
            # Review a snapshot, with no task-supplied conftest, sitecustomize or tests.
            snapshot = Path(temporary) / "candidate.py"
            shutil.copyfile(candidate, snapshot)
            # On Windows the venv redirector can leave its Python child holding
            # stdout open after timeout. The stdlib-only runner needs no venv.
            interpreter = str(Path(sys.base_prefix) / "python.exe") if os.name == "nt" else sys.executable
            command = [interpreter, "-I", "-S", str(runner), str(snapshot)]
            try:
                completed = subprocess.run(
                    command, cwd=temporary, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=self.timeout_seconds,
                    check=False,
                )
                exit_code: int | None = completed.returncode
                output = completed.stdout + completed.stderr
                completed_suite = "Ran 3 tests" in output and output.rstrip().endswith("OK")
                passed: bool | None = (exit_code == 0 and completed_suite)
                if exit_code == 0 and not completed_suite:
                    passed, exit_code = None, None
                    output += "\nNo completed independent acceptance suite; outcome unknown."
            except subprocess.TimeoutExpired:
                exit_code, passed = None, None
                output = "Independent verification timed out; outcome unknown."
            report.write_text(output, encoding="utf-8")
        return Verification(
            passed=passed, reviewer=reviewer, evidence=[report.as_uri()],
            command=command, exit_code=exit_code,
            summary="Fixed sample acceptance passed" if passed else output[-4000:],
        )
