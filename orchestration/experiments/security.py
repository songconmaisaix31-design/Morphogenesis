"""Fail-closed static and isolation gates for generated candidates.

Static scanning never proves safety; it is only the first gate before any
isolated execution is considered. Isolation capability is itemized and must be
*verified* by a real probe for the backend in use; a declared capability or a
mock backend must never be promoted to a real proof (``admitted`` is False until
``verified`` and ``probe == "passed"``).

This module is deliberately free of ``local_assets`` imports: ``local_assets``
depends on the experiment contracts, and importing the other direction would
create a package cycle. The deny-lists below mirror the frozen literal-files
``validate`` policy; the generated path additionally applies an allowlist-based
dependency gate (see ``static_checks``).
"""

from __future__ import annotations

import ast
import json
import re
from typing import Literal

from orchestration.experiments.generated import GeneratedExperimentPlan, IsolationReport, StaticSecurityReport
from orchestration.experiments.trusted import TrustedProbeRegistry

RESERVED_RUNNER_NAMES = frozenset({
    "output.json", "parameters.json", "runtime.json", "sandbox.json",
    "execution.json", "result.json", "generated-result.json", "plan.json",
})

SAFE_STDLIB = frozenset({
    "abc", "array", "bisect", "collections", "copy", "csv", "dataclasses", "decimal",
    "enum", "fractions", "functools", "heapq", "itertools", "json", "math", "numbers",
    "operator", "pathlib", "random", "re", "statistics", "string", "struct", "textwrap",
    "time", "typing", "unicodedata", "uuid",
})

_DANGEROUS = re.compile(
    r"\b(?:eval|exec|compile|__import__)\s*\(|\b(?:system|popen|unlink|rmtree|remove|"
    r"rmdir|chmod|chown|kill|spawn|fork)\s*\(|\b(?:curl|wget)\b|"
    r"rm\s+-[rf]|Remove-Item|Invoke-Expression", re.IGNORECASE,
)
_DANGEROUS_IMPORTS = frozenset({
    "subprocess", "socket", "ctypes", "multiprocessing", "requests", "httpx",
    "urllib", "http", "ftplib", "shutil", "importlib", "pickle", "marshal", "os",
})


class SecurityRejection(ValueError):
    """A generated candidate failed a static or isolation gate; execution is refused."""


def _top_level_imports(body: bytes, filename: str) -> set[str]:
    tree = ast.parse(body, filename=filename)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def static_checks(plan: GeneratedExperimentPlan, files: dict[str, bytes]) -> StaticSecurityReport:
    """Return a structured report; a single failure rejects execution (fail-closed)."""
    reasons: list[str] = []
    scope: Literal["pass", "fail"] = "pass"
    syntax: Literal["pass", "fail", "not_applicable"] = "pass"
    dependency: Literal["pass", "fail", "not_applicable"] = "pass"
    danger: Literal["pass", "fail"] = "pass"
    resource: Literal["pass", "fail"] = "pass"

    seen: set[str] = set()
    for name in files:
        if name in seen or name in RESERVED_RUNNER_NAMES or ".git" in name.split("/"):
            scope = "fail"
            reasons.append("reserved_or_duplicate_path:" + name)
        seen.add(name)

    total = sum(len(body) for body in files.values())
    if total > plan.backend.artifact_bytes or len(files) != len(plan.files):
        resource = "fail"
        reasons.append("code_size_or_manifest_count_exceeded")

    allowed = SAFE_STDLIB | set(plan.environment.dependencies)
    has_python = False
    for name, body in files.items():
        if name.endswith(".py"):
            has_python = True
            try:
                ast.parse(body, filename=name)
                compile(body, name, "exec")
            except (SyntaxError, ValueError):
                syntax = "fail"
                reasons.append("python_syntax:" + name)
                continue
            if _DANGEROUS.search(body.decode("utf-8", errors="replace")):
                danger = "fail"
                reasons.append("dangerous_pattern:" + name)
            imports = _top_level_imports(body, name)
            if any(name in _DANGEROUS_IMPORTS for name in imports):
                danger = "fail"
                reasons.append("dangerous_import:" + name)
            unapproved = imports - allowed
            if unapproved:
                dependency = "fail"
                reasons.append("unapproved_dependency:" + ",".join(sorted(unapproved)))
        elif name.endswith(".json"):
            try:
                json.loads(body.decode("utf-8"))
            except (ValueError, UnicodeError):
                syntax = "fail"
                reasons.append("json_syntax:" + name)
        else:
            syntax = "fail"
            reasons.append("unsupported_static_language:" + name)
    if not has_python:
        syntax = "fail"
        reasons.append("missing_python_entrypoint")

    return StaticSecurityReport(scope=scope, syntax=syntax, dependency=dependency,
                                danger=danger, resource=resource, reasons=tuple(reasons))


def verify_isolation(isolation: IsolationReport, registry: TrustedProbeRegistry | None) -> None:
    """Raise unless a host-owned registry proves the declared capability set.

    The report's own ``verified``/``probe`` booleans are advisory and ignored:
    only a matching ``TrustedProbeRegistry`` record (a real harmless probe) can
    admit execution. Absent proof, fail closed and never host-execute.
    """
    if not isolation.declared.complete:
        raise SecurityRejection("isolation_capability_incomplete")
    if registry is None or not registry.is_verified(isolation):
        raise SecurityRejection("isolation_capability_unverified")
