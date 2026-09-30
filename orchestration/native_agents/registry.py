"""Small native CLI registry and bounded, non-model discovery probes."""

import json
import os
import re
from pathlib import Path
import shutil
import subprocess

from contracts.base import Contract
from orchestration.native_agents.models import Capability, RuntimeId, RuntimeSpec


def _capabilities() -> dict[str, Capability]:
    return {
        key: Capability(supported=True, detail=detail)
        for key, detail in {
            "interactive": "Native TUI launch argv; caller supplies its terminal, no simulated PTY readiness",
            "headless": "Native CLI tool loop with JSONL output; model execution not run on A branch",
            "resume": "Explicit native session UUID; persistence retained, no automatic continuation",
            "mcp_stdio": "Session-local stdio config; actual tool connection requires integration gate",
            "stdin_prompt": "One text prompt in headless mode; attached/live bidirectional stdin not implemented",
            "owned_cancel": "Only the process launched by this adapter can be cancelled",
        }.items()
    } | {"sdk": Capability(supported=None, detail="No SDK imported or verified")}


REGISTRY: dict[RuntimeId, RuntimeSpec] = {
    "codex": RuntimeSpec(runtime="codex", executable="codex", npm_package="@openai/codex",
                         expected_version="0.159.0", auth_args=("login", "status"),
                         capabilities=_capabilities()),
    "claude": RuntimeSpec(runtime="claude", executable="claude", npm_package="@anthropic-ai/claude-code",
                          expected_version="2.1.238", auth_args=("auth", "status"),
                          capabilities=_capabilities()),
}


class ProbeResult(Contract):
    runtime: RuntimeId
    command: tuple[str, ...] | None = None
    version: str | None = None
    version_matches: bool | None = None
    authenticated: bool | None = None
    version_exit: int | None = None
    auth_exit: int | None = None
    error: str | None = None


def resolve_executable(spec: RuntimeSpec, *, platform: str | None = None,
                       executable: str | None = None) -> tuple[str, ...]:
    """Bypass Windows npm shims using the installed package's actual bin map.

    No shim parsing, cmd /c, PowerShell command strings, credential copying, or
    fallback to an unrelated runtime. Linux/WSL resolve their own PATH locally.
    """
    target = executable or shutil.which(spec.executable)
    if target is None:
        raise FileNotFoundError(f"{spec.executable} is not installed")
    path = Path(target).absolute()
    if not path.is_file():
        raise FileNotFoundError(f"executable does not exist: {path}")
    windows = (platform or os.name) in {"nt", "win32"}
    if windows and path.suffix.lower() in {".cmd", ".bat", ".ps1", ""}:
        package = path.parent / "node_modules" / spec.npm_package
        manifest = json.loads((package / "package.json").read_text(encoding="utf-8"))
        if manifest.get("name") != spec.npm_package:
            raise ValueError("npm package identity does not match the registry")
        bins = manifest.get("bin")
        relative = bins.get(spec.executable) if isinstance(bins, dict) else None
        if not isinstance(relative, str):
            raise ValueError("installed npm package has no matching bin entry")
        entry = (package / relative).resolve(strict=True)
        if not entry.is_relative_to(package.resolve()) or not entry.is_file():
            raise ValueError("npm bin entry escaped its package")
        if entry.suffix.lower() == ".exe":
            return (str(entry),)
        if entry.suffix.lower() in {".js", ".mjs", ".cjs"}:
            node = shutil.which("node")
            if node is None:
                raise FileNotFoundError("npm JavaScript entry requires node")
            if Path(node).suffix.lower() != ".exe":
                raise ValueError("Windows node must resolve to a native executable")
            return (node, str(entry))
        raise ValueError("npm bin is not a supported native or JavaScript entry")
    if windows and path.suffix.lower() != ".exe":
        raise ValueError("Windows executable must be native or a known npm shim")
    return (str(path),)


def child_environment() -> dict[str, str]:
    """Inherit official authentication locations; drop IDE dispatch authority."""
    return {key: value for key, value in os.environ.items() if not key.upper().startswith("ORCA_")}


def probe(runtime: RuntimeId) -> ProbeResult:
    spec = REGISTRY[runtime]
    command: tuple[str, ...] | None = None
    try:
        command = resolve_executable(spec)
        version = subprocess.run([*command, *spec.version_args], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=15,
                                 shell=False, env=child_environment())
        auth = subprocess.run([*command, *spec.auth_args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=15,
                              shell=False, env=child_environment())
        version_text = version.stdout.strip() if version.returncode == 0 else None
        measured_version = re.search(r"(?:^| )(\d+\.\d+\.\d+(?:[-+][^\s]+)?)(?: |$)", version_text or "")
        authenticated: bool | None = None
        if runtime == "claude" and auth.returncode in {0, 1}:
            try:
                value = json.loads(auth.stdout).get("loggedIn")
                authenticated = value if type(value) is bool else None
            except (ValueError, AttributeError):
                pass
        elif runtime == "codex":
            text = auth.stdout + auth.stderr
            if auth.returncode == 0 and "Logged in using" in text:
                authenticated = True
            elif "Not logged in" in text:
                authenticated = False
        return ProbeResult(runtime=runtime, command=command, version=version_text,
                           version_matches=measured_version.group(1) == spec.expected_version if measured_version else None,
                           authenticated=authenticated, version_exit=version.returncode,
                           auth_exit=auth.returncode)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        # Do not publish auth stdout, credentials, or timeout process arguments.
        return ProbeResult(runtime=runtime, command=command, error=type(exc).__name__)
