"""One place for the rule that child output never reaches a report verbatim."""

from __future__ import annotations

import re

#: A short, punctuation-restricted identifier: names, versions, exit statuses.
SAFE_TOKEN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 ._+()/:-]{0,63}\Z")

#: Only a version-shaped line may be echoed: ``<name> [v]X.Y[.Z...]``.  A bare
#: secret printed to stdout has no version tail, so it can never qualify.
VERSION_LINE = re.compile(r"\A[A-Za-z][A-Za-z0-9 ._+()-]{0,31} ?v?\d+(?:[.+-][0-9A-Za-z]+){1,4}\Z")


def safe_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text if SAFE_TOKEN.match(text) else None


def first_version_line(*chunks: bytes) -> str | None:
    """Return the first version-shaped line, or None. Never returns raw output."""
    for chunk in chunks:
        for raw in chunk.splitlines():
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            matched = VERSION_LINE.match(line)
            if matched is not None:
                return matched.group(0)
    return None
