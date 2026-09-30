"""Lossless normalization of official CLI JSONL; never infer scientific success."""

import json
import math
from typing import Literal

from contracts.identity import AttemptId

from contracts.results import Usage
from orchestration.native_agents.models import NativeEvent, RuntimeId


def _tokens(value: object, runtime: RuntimeId) -> int | None:
    if not isinstance(value, dict):
        return None
    keys = ["input_tokens", "output_tokens"]
    if runtime == "claude":
        keys += ["cache_creation_input_tokens", "cache_read_input_tokens"]
    numbers: list[int] = []
    for key in keys:
        number = value.get(key)
        if not isinstance(number, int) or isinstance(number, bool) or number < 0:
            return None
        numbers.append(number)
    return sum(numbers)


def _cost(value: object) -> float | None:
    if isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return float(value)
    return None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _reported_attempt(value: object) -> AttemptId | None:
    """Only parse B's explicit canonical field; do not manufacture identity from a Lease."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    if not isinstance(value, dict):
        return None
    payload = value
    nested = payload.get("result")
    if isinstance(nested, dict) and "attempt_id" not in payload:
        payload = nested
    try:
        return AttemptId.model_validate(payload["attempt_id"])
    except (ValueError, KeyError):
        return None


def parse_event(runtime: RuntimeId, line: str) -> list[NativeEvent]:
    """Unknown lines and fields survive in raw; one Claude event can contain many tools."""
    if runtime not in {"codex", "claude"}:
        raise ValueError("runtime has no native event adapter")
    try:
        raw = json.loads(line)
    except ValueError:
        raw = line
    if not isinstance(raw, dict):
        return [NativeEvent(runtime=runtime, kind="unknown", raw=raw)]
    native_type = _text(raw.get("type"))
    session = _text(raw.get("thread_id" if runtime == "codex" else "session_id"))
    kind: Literal["session", "turn", "tool", "tool_result", "message", "result", "error", "unknown"] = "unknown"
    terminal: Literal["completed", "failed"] | None = None
    usage = Usage()
    if runtime == "codex":
        if native_type == "thread.started":
            kind = "session"
        elif native_type in {"turn.started", "turn.completed"}:
            kind = "turn"
            if native_type == "turn.completed":
                terminal = "completed"
                usage = Usage(tokens=_tokens(raw.get("usage"), runtime))
        elif native_type in {"turn.failed", "error"}:
            kind = "error"
            terminal = "failed"
        elif native_type in {"item.started", "item.updated", "item.completed"}:
            item = raw.get("item")
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"command_execution", "mcp_tool_call", "web_search", "file_change", "collab_tool_call"}:
                    result = item.get("result")
                    reported_attempt = _reported_attempt(result.get("structured_content")) if isinstance(result, dict) else None
                    return [NativeEvent(runtime=runtime, kind="tool_result" if native_type == "item.completed" else "tool", native_type=native_type,
                                        tool_id=_text(item.get("id")),
                                        reported_attempt=reported_attempt,
                                        tool_name=_text(item.get("tool")) or _text(item_type), raw=raw)]
                if item_type in {"agent_message", "reasoning"}:
                    kind = "message"
    else:
        if native_type == "system" and raw.get("subtype") == "init":
            kind = "session"
        elif native_type == "result":
            kind = "result"
            error = raw.get("is_error")
            if error is True or (_text(raw.get("subtype")) or "").startswith("error_"):
                terminal = "failed"
            elif error is False and raw.get("subtype") == "success":
                terminal = "completed"
            usage = Usage(tokens=_tokens(raw.get("usage"), runtime),
                          cost_usd=_cost(raw.get("total_cost_usd")))
        elif native_type in {"assistant", "user"}:
            kind = "message"
            message = raw.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            tools: list[NativeEvent] = []
            if native_type == "assistant" and isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_use":
                        tools.append(NativeEvent(runtime=runtime, kind="tool", native_type=native_type,
                                                 session_id=session, tool_id=_text(item.get("id")),
                                                 tool_name=_text(item.get("name")), raw=raw))
            if tools:
                return tools
            if native_type == "user" and isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        attempt = _reported_attempt(raw.get("tool_use_result")) or _reported_attempt(item.get("content"))
                        if attempt is None and isinstance(item.get("content"), list):
                            for block in item["content"]:
                                if isinstance(block, dict):
                                    attempt = _reported_attempt(block.get("text"))
                                    if attempt:
                                        break
                        tools.append(NativeEvent(runtime=runtime, kind="tool_result", native_type=native_type,
                                                 session_id=session, tool_id=_text(item.get("tool_use_id")),
                                                 reported_attempt=attempt, raw=raw))
                if tools:
                    return tools
        elif native_type == "error":
            kind = "error"
    return [NativeEvent(runtime=runtime, kind=kind, native_type=native_type, session_id=session,
                        terminal=terminal, usage=usage, raw=raw)]
