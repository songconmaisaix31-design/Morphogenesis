"""Narrow behavioral adaptations of stablyai/orca (MIT).

Source: 85f8d6b5f507df795cd3cef1cdea08124cf801ee, src/shared/
print-mode-headless-command.ts and agent-process-recognition.ts.
Changes: typed argv only, two CLI names, no desktop process enumeration.
Recognition is descriptive and MUST NEVER confer cancellation ownership.
See ORCA_LICENSE.txt and docs/agents/upstream.md for original tests and scope.
"""

import re
from collections.abc import Sequence

from orchestration.native_agents.models import RuntimeId

ORCA_SHA = "85f8d6b5f507df795cd3cef1cdea08124cf801ee"


def is_print_headless(tokens: Sequence[str]) -> bool:
    """Port of isPrintModeHeadlessOneShotCommand, including option terminator."""
    for index in range(1, len(tokens)):
        token = tokens[index]
        if token == "--":
            return False
        name, separator, value = token.partition("=")
        if name in {"--print", "-p"}:
            return True
        if name == "--output-format":
            value = value if separator else (tokens[index + 1] if index + 1 < len(tokens) else "")
            if value.lower() in {"json", "stream-json"}:
                return True
    return False


def recognize_process(name: str | None) -> RuntimeId | None:
    """Port of the upstream basename/extension and packaged-Codex rules."""
    normalized = re.split(r"[\\/]", (name or "").strip().strip("\"'"))[-1].lower()
    normalized = re.sub(r"\.(exe|cmd|bat|ps1)$", "", normalized)
    if normalized == "codex" or normalized.startswith("codex-"):
        return "codex"
    if normalized == "claude":
        return "claude"
    return None
