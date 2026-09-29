"""Shared single-request EvoMap transport, extracted from gateway @605cf48.

Repository Apache-2.0; no retry, redirect, environment proxy or tool loop.
The caller owns authorization, reservations, input limits and durable intent.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time

import httpx
from pydantic import JsonValue

EVOMAP_BASE_URL = "https://api.evomap.ai/v1"
EVOMAP_MODEL = "evomap-gpt-5.6-luna"
MAX_RESPONSE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class GatewayResponse:
    status: int | None
    body: JsonValue
    error_kind: str | None
    elapsed_seconds: float
    finished_at: float
    request_id: str | None = None


def single_request(payload: dict[str, JsonValue], *, key: str, phase_timeout: float,
                   transport: httpx.MockTransport | None = None) -> GatewayResponse:
    """One POST only; phase timeouts do not constitute an in-flight cost bound."""
    if not 0 < phase_timeout <= 180:
        raise ValueError("invalid_gateway_timeout")
    status: int | None = None
    error_kind: str | None = None
    request_id: str | None = None
    raw = bytearray()
    started = time.monotonic()
    try:
        with httpx.Client(transport=transport, trust_env=False, follow_redirects=False,
                          timeout=httpx.Timeout(phase_timeout)) as client:
            with client.stream("POST", EVOMAP_BASE_URL + "/chat/completions", json=payload,
                               headers={"Authorization": f"Bearer {key}"}) as response:
                status = response.status_code
                identifier = response.headers.get("x-request-id")
                if identifier is not None and re.fullmatch(r"[A-Za-z0-9_.:/-]{1,200}", identifier) and key not in identifier:
                    request_id = identifier
                for chunk in response.iter_bytes():
                    remaining = MAX_RESPONSE_BYTES - len(raw)
                    raw.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        error_kind = "response_too_large"
                        break
    except httpx.HTTPError as exc:
        error_kind = type(exc).__name__
    elapsed = time.monotonic() - started
    try:
        body: JsonValue = json.loads(raw)
    except (ValueError, UnicodeError):
        body = raw.decode("utf-8", errors="replace")
    if request_id is None and isinstance(body, dict):
        identifier = body.get("id")
        if isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9_.:/-]{1,200}", identifier) and key not in identifier:
            request_id = identifier
    return GatewayResponse(status, body, error_kind, elapsed, time.time(), request_id)
