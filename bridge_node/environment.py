"""Small, explicit child environment: no ambient credentials or Node injection."""

from __future__ import annotations

import os
from pathlib import Path


def child_environment(workspace: Path) -> dict[str, str]:
    # Preserve only OS process discovery essentials. No app tokens or proxies.
    keep = {"path", "systemroot", "windir", "comspec", "pathext"}
    env = {key: value for key, value in os.environ.items() if key.lower() in keep}
    root = workspace.resolve()
    home = root / "home"
    temp = root / "tmp"
    for directory in (home, temp):
        directory.mkdir(parents=True, exist_ok=True)
    env.update({
        "HOME": str(home), "USERPROFILE": str(home),
        "HOMEDRIVE": home.drive, "HOMEPATH": str(home)[len(home.drive):],
        "APPDATA": str(home / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(home / "AppData" / "Local"),
        "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
        # Explicit empties also override Python MCP SDK default environment.
        "NODE_OPTIONS": "", "NODE_PATH": "",
        "EVOMAP_API_KEY": "", "EVOMAP_NODE_SECRET": "", "EVOMAP_NODE_ID": "",
        "EVOMAP_HUB_URL": "http://127.0.0.1:9",
        "GEP_ASSETS_DIR": str(root / "assets"),
        "GEP_MEMORY_DIR": str(root / "memory"),
        "EVOLVER_SKILLS_DIR": str(root / "skills" / "bundled"),
        "CLAUDE_SKILLS_DIR": str(root / "skills" / "local"),
    })
    return env
