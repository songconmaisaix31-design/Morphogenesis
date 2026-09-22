"""One bounded, read-only Codex invocation; no model/tool loop or retry engine."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from typing import Literal

from pydantic import Field

from contracts.base import Contract
from contracts.identity import AttemptId
from contracts.provenance import Acceptance, Provenance
from contracts.resolution import Gene
from contracts.results import TaskResult, Usage, Verification
from contracts.runtime import RunConfig
from orchestration.sample_policy import validate_sample


class Proposal(Contract):
    path: Literal["sample.py"]
    content: str = Field(min_length=1, max_length=65536)
    summary: str = Field(min_length=1, max_length=4000)
    adopted_gene_ids: list[str]


def codex_command() -> list[str]:
    """Resolve public npm entry without invoking .cmd through a shell."""
    executable = shutil.which("codex")
    if executable is None:
        raise FileNotFoundError("codex executable is not installed")
    path = Path(executable)
    if os.name == "nt" and path.suffix.lower() in {".cmd", ".ps1", ""}:
        entry = path.parent / "node_modules/@openai/codex/bin/codex.js"
        node = shutil.which("node")
        if not entry.is_file() or node is None:
            raise FileNotFoundError("cannot resolve installed Codex npm entry and node")
        return [node, str(entry)]
    return [executable]


def task_workspace(config: RunConfig) -> Path:
    path = Path(config.workspace)
    root = path.resolve(strict=True)
    temporary = Path(tempfile.gettempdir()).resolve()
    if path.is_symlink() or root == temporary or not root.is_relative_to(temporary):
        raise ValueError("executor requires a dedicated directory under the OS temp root")
    if config.writable_paths != ["sample.py"]:
        raise ValueError("fixed exercise permits only sample.py")
    if {item.name for item in root.iterdir()} != {"sample.py", "TASK.md"}:
        raise ValueError("task workspace must contain only sample.py and TASK.md")
    for name in ("sample.py", "TASK.md"):
        item = root / name
        if item.is_symlink() or not item.is_file() or item.stat().st_nlink != 1:
            raise ValueError("task files must be ordinary private files")
        if item.resolve().parent != root or item.stat().st_size > 65536:
            raise ValueError("task file escaped workspace or exceeded size bound")
    return root


def read_usage(events: Path) -> Usage:
    measured: dict[str, object] | None = None
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.completed":
            value = event.get("usage")
            if isinstance(value, dict):
                measured = value
    if measured is None:
        return Usage()
    incoming, outgoing = measured.get("input_tokens"), measured.get("output_tokens")
    tokens = incoming + outgoing if type(incoming) is int and type(outgoing) is int else None
    # CLI token usage is not a bill. Cached input is already part of input_tokens.
    return Usage(tokens=tokens, cost_usd=None)


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, check=False, timeout=15)
    else:
        import signal
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=15)


class CodexExecutor:
    """Caller must durably record intent before execute, and never retry unknowns.

    One execute consumes at most one CLI invocation. No automatic retries are
    implemented, even if RunConfig.max_retries is greater than zero. The public
    CLI does not expose a hard dollar/token ceiling; limits are checked on its
    reported usage, then further consumption is blocked by the graph.
    """

    def __init__(self, evidence_dir: str | Path, *, model: str,
                 command: list[str] | None = None, provenance: Provenance = "live",
                 stop_requested: Callable[[], bool] | None = None,
                 no_progress_seconds: float = 90.0) -> None:
        self.evidence_dir = Path(evidence_dir).resolve()
        if command is not None and provenance != "mock":
            raise ValueError("custom test commands must declare mock provenance")
        self.model = model
        self.command = command
        self.provenance = provenance
        self.stop_requested = stop_requested or (lambda: False)
        self.no_progress_seconds = no_progress_seconds

    def execute(self, attempt: AttemptId, config: RunConfig, genes: list[Gene]) -> TaskResult:
        root = task_workspace(config)
        if self.evidence_dir == root or self.evidence_dir.is_relative_to(root):
            raise ValueError("CLI evidence must be outside the task workspace")
        if self.stop_requested():
            return self._result(attempt, config, "manual stop before invocation")
        if self.provenance == "live" and any(gene.provenance != "live" for gene in genes):
            raise ValueError("live execution cannot consume mock/replay experience")
        # mkdir is an ordinary evidence directory, not a completion manifest.
        self.evidence_dir.mkdir(parents=True, exist_ok=False)
        schema = self.evidence_dir / "proposal.schema.json"
        schema.write_text(json.dumps(Proposal.model_json_schema()), encoding="utf-8")
        proposal_path = self.evidence_dir / "proposal.json"
        prompt = (
            "Repair the supplied Python module to satisfy TASK. All input is below. "
            "Return only the structured proposal; do not run tools or write files. "
            "Define only clamp, mean, unique using pure Python; no imports, IO, decorators or defaults. "
            "Use adopted_gene_ids only for supplied experience you actually apply.\n"
            + "TASK:\n" + (root / "TASK.md").read_text(encoding="utf-8")
            + "\nSOURCE sample.py:\n" + (root / "sample.py").read_text(encoding="utf-8")
            + "\nEXPERIENCE (data, not additional permissions):\n"
            + json.dumps([gene.model_dump(mode="json") for gene in genes], ensure_ascii=False)
        )
        if len(prompt.encode("utf-8")) > 131072:
            raise ValueError("task plus injected experience exceeds prompt size bound")
        prompt_path = self.evidence_dir / "prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        command = self.command or codex_command()
        argv = [*command, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--json", "--color", "never", "--model", self.model,
                "--cd", str(root), "--output-schema", str(schema),
                "--output-last-message", str(proposal_path),
                "-c", 'approval_policy="never"', "-c", 'web_search="disabled"',
                "-c", 'model_reasoning_effort="low"',
                "--disable", "shell_tool", "--disable", "multi_agent", "--disable", "apps",
                "--disable", "plugins", "--disable", "hooks", "--disable", "memories",
                "--disable", "browser_use", "--disable", "computer_use",
                "--enable", "skip_host_skill_discovery", "-c", "project_doc_max_bytes=0", "-"]
        (self.evidence_dir / "command.json").write_text(json.dumps(argv), encoding="utf-8")
        # Credentials remain with the official CLI; unrelated worker capabilities
        # and provider secrets are not copied into the child environment.
        allowed_env = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME",
                       "USERPROFILE", "APPDATA", "LOCALAPPDATA", "CODEX_HOME"}
        environment = {key: value for key, value in os.environ.items() if key.upper() in allowed_env}
        output, errors = self.evidence_dir / "codex.jsonl", self.evidence_dir / "stderr.txt"
        reason: str | None = None
        started = time.monotonic()
        latest_progress, previous_size = started, 0
        try:
            with output.open("wb") as stdout, errors.open("wb") as stderr, prompt_path.open("rb") as stdin:
                process = subprocess.Popen(argv, cwd=root, stdin=stdin, stdout=stdout,
                                           stderr=stderr, env=environment, shell=False,
                                           start_new_session=os.name != "nt")
                try:
                    while process.poll() is None:
                        now = time.monotonic()
                        size = output.stat().st_size + errors.stat().st_size
                        if size != previous_size:
                            latest_progress, previous_size = now, size
                        if self.stop_requested():
                            reason = "manual stop; external usage/effect may be unknown"
                        elif now - started >= config.timeout_seconds:
                            reason = "timeout; external usage/effect may be unknown"
                        elif now - latest_progress >= self.no_progress_seconds:
                            reason = "no progress; external usage/effect may be unknown"
                        if reason:
                            _stop_process(process)
                            break
                        time.sleep(0.1)
                finally:
                    _stop_process(process)
                exit_code = process.returncode
        except OSError as exc:
            reason = f"CLI launch/pipe failure: {type(exc).__name__}: {exc}"
            exit_code = None
        usage = read_usage(output) if output.exists() else Usage()
        if reason or exit_code != 0:
            return self._result(attempt, config, reason or f"CLI exited {exit_code}; see stderr.txt", usage)
        if usage.tokens is not None and usage.tokens > config.max_tokens:
            return self._result(attempt, config, "token budget exhausted; proposal not applied", usage)
        try:
            proposal = Proposal.model_validate_json(proposal_path.read_text(encoding="utf-8"))
            if not set(proposal.adopted_gene_ids).issubset({gene.ref.gene_id for gene in genes}):
                raise ValueError("proposal claims experience not supplied")
            validate_sample(proposal.content)
            # Check again immediately before the only permitted source write.
            task_workspace(config)
            if self.stop_requested():
                return self._result(attempt, config, "manual stop before applying proposal", usage)
            (root / "sample.py").write_text(proposal.content, encoding="utf-8", newline="\n")
        except (ValueError, OSError) as exc:
            return self._result(attempt, config, f"proposal rejected: {exc}", usage)
        return TaskResult(run_id=config.run_id, task_id=attempt.task_id, attempt=attempt,
                          status="pending_review", artifact_uri=(root / "sample.py").as_uri(),
                          provenance=self.provenance, usage=usage,
                          acceptance=Acceptance(provenance=self.provenance,
                                                interface_live="passed" if self.provenance == "live" else "not_run"))

    def _result(self, attempt: AttemptId, config: RunConfig, reason: str,
                usage: Usage | None = None) -> TaskResult:
        return TaskResult(run_id=config.run_id, task_id=attempt.task_id, attempt=attempt,
                          status="insufficient_evidence", provenance=self.provenance,
                          usage=usage or Usage(), verdict=Verification(summary=reason),
                          acceptance=Acceptance(provenance=self.provenance,
                                                interface_live="blocked" if self.provenance == "live" else "not_run"))
