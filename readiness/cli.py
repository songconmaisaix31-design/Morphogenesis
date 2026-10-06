"""Run one declared public CLI once and report its exit status.

The adapter never invents command lines.  Which executable, which arguments and
whether a non-zero exit means "not installed yet" or "broken" are deployment
decisions declared in a manifest, because those details belong to the CLI's own
published contract.
"""

from __future__ import annotations

import math
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from contracts.readiness import ProbeResult, ProbeState, ProbeSubject
from readiness.launch import EnvMode, plan_launch
from readiness.sanitize import first_version_line


@dataclass(frozen=True)
class PublicCliProbe:
    """Invoke an allowlisted executable with declared arguments, once."""

    probe_id: str
    command: str
    args: Sequence[str] = ()
    subject: ProbeSubject = "interface"
    timeout_seconds: float = 5.0
    nonzero_state: ProbeState = "failed"
    env_mode: EnvMode = "isolated"
    report_version_line: bool = False
    workspace_root: Path | None = None

    def __post_init__(self) -> None:
        if not self.probe_id:
            raise ValueError("probe_id must not be empty")
        if not self.command or "\x00" in self.command:
            raise ValueError("command must be a non-empty executable name or path")
        if any("\x00" in arg for arg in self.args):
            raise ValueError("arguments must not contain NUL")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        if self.nonzero_state == "not_run":
            raise ValueError("nonzero_state must describe an observation")

    def probe(self) -> ProbeResult:
        executable = shutil.which(self.command)
        if executable is None:
            return self._result("blocked", f"未找到公开 CLI：{self.command}", {"code": "command_missing"})
        plan = plan_launch(self.env_mode, self.workspace_root)
        try:
            completed = subprocess.run(
                [executable, *self.args],
                cwd=plan.cwd,
                env=plan.env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._result("failed", "探测命令超时，未重试", {"code": "timeout"})
        except OSError:
            return self._result("failed", "无法启动探测命令", {"code": "spawn_failed"})
        finally:
            plan.cleanup()

        state: ProbeState = "ok" if completed.returncode == 0 else self.nonzero_state
        evidence = {
            "code": "exit_ok" if completed.returncode == 0 else "exit_nonzero",
            "exit_code": str(completed.returncode),
        }
        detail = f"{self.command} 退出码 {completed.returncode}"
        if self.report_version_line:
            line = first_version_line(completed.stdout, completed.stderr)
            if line is not None:
                evidence["output"] = line
                if completed.returncode == 0:
                    detail = f"{self.command} {line}"
        return self._result(state, detail, evidence)

    def _result(self, state: ProbeState, detail: str, evidence: dict[str, str]) -> ProbeResult:
        return ProbeResult(
            probe_id=self.probe_id,
            subject=self.subject,
            state=state,
            observed=True,
            detail=detail,
            evidence=evidence,
            notes=[f"每次报告最多执行一次；环境模式：{self.env_mode}。"],
        )
