"""Launch rules shared by the CLI and MCP probes.

``isolated`` (the default) mirrors the posture the Node bridge already uses: a
scratch directory, HOME/TEMP inside it, ambient credentials cleared.  ``inherit``
runs the probe as the operator, which is the only way a probe can answer "is my
account signed in?"; it is opt-in per probe and never assumed.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from bridge_node.environment import child_environment

EnvMode = Literal["isolated", "inherit"]
SCRATCH_PREFIX = "morph-readiness-"


@dataclass(frozen=True)
class LaunchPlan:
    cwd: str | None
    env: dict[str, str]
    scratch: Path | None

    def cleanup(self) -> None:
        if self.scratch is not None:
            shutil.rmtree(self.scratch, ignore_errors=True)


def plan_launch(mode: EnvMode, workspace_root: Path | None = None) -> LaunchPlan:
    if mode == "inherit":
        root = workspace_root.resolve() if workspace_root is not None else None
        return LaunchPlan(cwd=None if root is None else str(root), env=dict(os.environ), scratch=None)
    if workspace_root is not None:
        root = workspace_root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        return LaunchPlan(cwd=str(root), env=child_environment(root), scratch=None)
    scratch = Path(tempfile.mkdtemp(prefix=SCRATCH_PREFIX))
    return LaunchPlan(cwd=str(scratch), env=child_environment(scratch), scratch=scratch)
