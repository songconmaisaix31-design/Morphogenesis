"""One bounded model boundary shared by the genuine benchmark runtimes.

The gate limits requests; it does not select tasks or schedule framework work.
Keys enter each owning process in memory and are never part of a serializable
configuration. HTTP overlap is client-observed activity, not GPU concurrency.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
import json
import math
from multiprocessing.context import BaseContext
import os
import re
import time
from typing import Any, Literal
from uuid import uuid4

import httpx

STEPFUN_URL = "https://api.stepfun.com/v1/chat/completions"
STEPFUN_MODEL = "step-3.5-flash"
ANSWER_FORMAT_INSTRUCTION = (
    "The final line must be #### followed by one space and the numeric answer only "
    "(example: #### 42). Replace the number with your result. "
    "No word answer, currency sign, units, colon, or LaTeX on that line. "
    "Use the marker only once."
)
SYSTEM_PROMPT = (
    "You are a careful mathematics solver. Solve the supplied problem without tools. "
    + ANSWER_FORMAT_INSTRUCTION
)
MAX_REQUESTS = 732
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,160}")
_KEY = re.compile(r"[A-Za-z0-9._~+/=-]{1,8192}")


@dataclass(frozen=True, kw_only=True)
class ModelRequest:
    run_id: str
    framework: str
    block_id: str
    seed: int
    task_id: str
    prompt: str
    max_tokens: int
    temperature: float
    role: str = "solver"
    attempt: int = 1

    def __post_init__(self) -> None:
        for value in (self.run_id, self.framework, self.block_id, self.task_id, self.role):
            if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
                raise ValueError("invalid_benchmark_identity")
        if type(self.seed) is not int or not 0 <= self.seed <= 2**31 - 1:
            raise ValueError("invalid_benchmark_seed")
        if type(self.attempt) is not int or self.attempt != 1:
            raise ValueError("benchmark_requires_one_attempt")
        if not isinstance(self.prompt, str) or not self.prompt or len(self.prompt.encode("utf-8")) > 48000:
            raise ValueError("invalid_benchmark_prompt")
        if type(self.max_tokens) is not int or not 1 <= self.max_tokens <= 4096:
            raise ValueError("invalid_benchmark_output_limit")
        if (type(self.temperature) not in (int, float) or not math.isfinite(self.temperature)
                or not 0 <= self.temperature <= 2):
            raise ValueError("invalid_benchmark_temperature")


@dataclass(frozen=True)
class ModelResponse:
    text: str | None
    usage: dict[str, int] | None
    status: Literal["completed", "error", "canceled", "fatal"]
    request_id: str | None
    evidence: dict[str, Any]


@dataclass(frozen=True)
class SharedRequestGate:
    """Multiprocessing primitives, deliberately containing no credential."""

    concurrency: int
    max_requests: int
    clock_id: str
    semaphore: Any
    lock: Any
    reserved: Any
    active: Any
    peak: Any
    stopped: Any
    owner_pid: int
    generation: int
    current_generation: Any

    @classmethod
    def create(cls, context: BaseContext, *, concurrency: int, max_requests: int) -> SharedRequestGate:
        if type(concurrency) is not int or not 1 <= concurrency <= 5:
            raise ValueError("benchmark_concurrency_must_be_1_to_5")
        if type(max_requests) is not int or not 1 <= max_requests <= MAX_REQUESTS:
            raise ValueError("benchmark_request_cap_must_be_1_to_732")
        return cls(concurrency, max_requests, uuid4().hex,
                   context.BoundedSemaphore(concurrency), context.Lock(),
                   context.Value("q", 0, lock=False), context.Value("q", 0, lock=False),
                   context.Value("q", 0, lock=False), context.Event(), os.getpid(), 0,
                   context.Value("q", 0, lock=False))

    def for_concurrency(self, context: BaseContext, concurrency: int) -> SharedRequestGate:
        """After native runtime drain, replace only the next arm's permit limit."""
        if os.getpid() != self.owner_pid:
            raise ValueError("request_gate_reconfiguration_parent_only")
        if type(concurrency) is not int or not 1 <= concurrency <= 5:
            raise ValueError("benchmark_concurrency_must_be_1_to_5")
        with self.lock:
            if self.active.value != 0:
                raise ValueError("request_gate_has_active_requests")
            if self.stopped.is_set():
                raise ValueError("request_gate_already_stopped")
            if self.generation != self.current_generation.value:
                raise ValueError("request_gate_generation_stale")
            semaphore = context.BoundedSemaphore(concurrency)
            self.current_generation.value += 1
            return SharedRequestGate(concurrency, self.max_requests, self.clock_id,
                semaphore, self.lock, self.reserved, self.active, self.peak, self.stopped,
                self.owner_pid, int(self.current_generation.value), self.current_generation)

    def stop(self) -> None:
        self.stopped.set()

    def snapshot(self) -> dict[str, int | bool | str]:
        with self.lock:
            return {"concurrency": self.concurrency, "request_cap": self.max_requests,
                    "reserved_requests": int(self.reserved.value), "active_reservations": int(self.active.value),
                    "peak_active_reservations": int(self.peak.value), "stopped": bool(self.stopped.is_set()),
                    "clock_id": self.clock_id, "gate_generation": self.generation,
                    "current_gate_generation": int(self.current_generation.value)}


def request_payload(request: ModelRequest) -> dict[str, Any]:
    """Framework labels and gold never enter the model's context."""
    return {"model": STEPFUN_MODEL, "stream": False, "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": request.prompt}]}


def validate_transport_configuration() -> None:
    """Validate installed proxy/TLS transport support before reading any key."""
    async def probe() -> None:
        async with httpx.AsyncClient(trust_env=True, follow_redirects=False,
                                     timeout=httpx.Timeout(120)):
            # 仅初始化并关闭客户端，不建立连接或发送请求。
            pass

    try:
        asyncio.run(probe())
    except Exception:
        raise RuntimeError("transport_initialization_failure") from None


class StepFunBenchmarkExecutor:
    def __init__(self, key: str, gate: SharedRequestGate, *, timeout_seconds: float = 120,
                 transport: httpx.MockTransport | None = None,
                 provenance: Literal["live", "mock"] = "live") -> None:
        if not isinstance(key, str) or _KEY.fullmatch(key) is None:
            raise ValueError("invalid_ephemeral_credential")
        if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
                or not 0 < timeout_seconds <= 180):
            raise ValueError("invalid_benchmark_timeout")
        if (transport is None) != (provenance == "live") or (transport is not None and not isinstance(transport, httpx.MockTransport)):
            raise ValueError("benchmark_transport_provenance_mismatch")
        self._key = key
        self.gate = gate
        self.timeout_seconds = timeout_seconds
        self._transport = transport
        self.provenance = provenance

    def __getstate__(self) -> Any:
        raise TypeError("ephemeral_executor_must_not_be_serialized")

    def close(self) -> None:
        # 丢弃本对象引用；不宣称对 Python 不可变字符串执行了物理内存清零。
        self._key = ""

    def generate_sync(self, request: ModelRequest) -> ModelResponse:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.generate(request))
        raise RuntimeError("use_async_generate_in_running_event_loop")

    async def generate(self, request: ModelRequest) -> ModelResponse:
        queued = time.monotonic_ns()
        evidence: dict[str, Any] = {
            "schema": "morph.benchmark-request.v1", "provenance": self.provenance,
            "run_id": request.run_id, "framework": request.framework, "block_id": request.block_id,
            "task_id": request.task_id, "role": request.role, "attempt": request.attempt,
            "order_seed": request.seed, "pid": os.getpid(),
            "admission_limit": self.gate.concurrency, "gate_generation": self.gate.generation,
            "clock": {"kind": "host-monotonic", "id": self.gate.clock_id,
                      "implementation": time.get_clock_info("monotonic").implementation},
            "interval_scope": "client_observed_http_active_not_model_or_gpu_execution",
            "queued_at_ns": queued, "permit_acquired_at_ns": None, "http_entered_at_ns": None,
            "response_headers_at_ns": None, "first_body_byte_at_ns": None, "last_body_byte_at_ns": None,
            "http_returned_at_ns": None,
            "first_stream_delta_at_ns": None, "last_stream_delta_at_ns": None, "ended_at_ns": None,
            "http_status": None, "provider_request_id": None, "returned_model": None,
            "retry_after_seconds": None, "retry_count": 0, "billing_cost": None,
            "error_kind": None, "unknown_remote_effect": False, "model_outcome": None,
        }
        acquired = False
        reserved = False
        entered = False
        key = self._key

        def finish(status: Literal["completed", "error", "canceled", "fatal"], *,
                   text: str | None = None, usage: dict[str, int] | None = None,
                   request_id: str | None = None, error: str | None = None,
                   unknown: bool = False) -> ModelResponse:
            if status == "fatal":
                self.gate.stop()
            evidence.update(ended_at_ns=time.monotonic_ns(), error_kind=error,
                            unknown_remote_effect=unknown)
            # 所有可持久化字段最后再检查一次，不返回服务端异常原文。
            if key and key in json.dumps([text, usage, request_id, evidence], ensure_ascii=False):
                self.gate.stop()
                evidence.clear()
                evidence.update({
                    "schema": "morph.benchmark-request.v1", "provenance": self.provenance,
                    "error_kind": "credential_echo", "unknown_remote_effect": entered,
                    "ended_at_ns": time.monotonic_ns(), "retry_count": 0})
                return ModelResponse(None, None, "fatal", None, evidence)
            return ModelResponse(text, usage, status, request_id, evidence)

        try:
            if not key:
                return finish("fatal", error="ephemeral_credential_closed")
            payload = request_payload(request)
            rendered = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            if key.encode("utf-8") in rendered or key in json.dumps(evidence, ensure_ascii=False):
                return finish("fatal", error="credential_in_input")
            evidence["request_settings"] = {"url": STEPFUN_URL, "model": STEPFUN_MODEL,
                "system_prompt": SYSTEM_PROMPT, "max_tokens": request.max_tokens,
                "temperature": request.temperature, "stream": False, "tools": None,
                "reasoning_effort": None, "provider_seed": None}
            evidence["payload_sha256"] = hashlib.sha256(rendered).hexdigest()
            async with asyncio.timeout(self.timeout_seconds):
                while not acquired:
                    if self.gate.stopped.is_set():
                        return finish("fatal", error="shared_request_gate_stopped")
                    acquired = bool(self.gate.semaphore.acquire(False))
                    if not acquired:
                        # 只等待真实账户准入；不改变任务工作量或制造运行重叠。
                        await asyncio.sleep(0.01)
                evidence["permit_acquired_at_ns"] = time.monotonic_ns()
                with self.gate.lock:
                    if self.gate.stopped.is_set():
                        return finish("fatal", error="shared_request_gate_stopped")
                    if self.gate.generation != self.gate.current_generation.value:
                        return finish("fatal", error="stale_request_gate")
                    if self.gate.reserved.value >= self.gate.max_requests:
                        return finish("fatal", error="shared_request_budget_exhausted")
                    self.gate.reserved.value += 1
                    self.gate.active.value += 1
                    self.gate.peak.value = max(self.gate.peak.value, self.gate.active.value)
                    evidence["request_ordinal"] = int(self.gate.reserved.value)
                    reserved = True
                # 现有受信代理/CA 可供 httpx 使用；TLS 校验保留，禁止重定向与自动重试。
                async with httpx.AsyncClient(transport=self._transport, trust_env=True,
                        follow_redirects=False, timeout=httpx.Timeout(self.timeout_seconds)) as client:
                    evidence["http_entered_at_ns"] = time.monotonic_ns()
                    entered = True
                    async with client.stream("POST", STEPFUN_URL, json=payload,
                            headers={"Authorization": "Bearer " + key}) as response:
                        evidence["response_headers_at_ns"] = time.monotonic_ns()
                        evidence["http_status"] = response.status_code
                        identifier = response.headers.get("x-request-id")
                        if identifier and key not in identifier and _IDENTIFIER.fullmatch(identifier):
                            evidence["provider_request_id"] = identifier
                        retry_after = response.headers.get("retry-after", "")
                        if re.fullmatch(r"[0-9]{1,5}(?:\.[0-9]{1,3})?", retry_after):
                            evidence["retry_after_seconds"] = float(retry_after)
                        raw = bytearray()
                        async for chunk in response.aiter_bytes():
                            now = time.monotonic_ns()
                            if chunk:
                                if evidence["first_body_byte_at_ns"] is None:
                                    evidence["first_body_byte_at_ns"] = now
                                evidence["last_body_byte_at_ns"] = now
                            if len(raw) + len(chunk) > MAX_RESPONSE_BYTES:
                                return finish("fatal", error="response_too_large", unknown=True)
                            raw.extend(chunk)
                        if key.encode("utf-8") in raw:
                            return finish("fatal", error="credential_echo", unknown=True)
                        if response.status_code != 200:
                            return finish("fatal", error="provider_rate_limit" if response.status_code == 429
                                          else "provider_http_error", unknown=response.status_code >= 500)
                evidence["http_returned_at_ns"] = time.monotonic_ns()
                try:
                    body = json.loads(raw)
                except (ValueError, UnicodeError):
                    return finish("fatal", error="invalid_provider_json", unknown=True)
                if key in json.dumps(body, ensure_ascii=False):
                    return finish("fatal", error="credential_echo", unknown=True)
                if not isinstance(body, dict):
                    return finish("fatal", error="invalid_provider_response", unknown=True)
                returned_model = body.get("model")
                if returned_model != STEPFUN_MODEL:
                    return finish("fatal", error="unexpected_provider_model", unknown=True)
                evidence["returned_model"] = returned_model
                identifier = body.get("id")
                if evidence["provider_request_id"] is None and isinstance(identifier, str) and _IDENTIFIER.fullmatch(identifier):
                    evidence["provider_request_id"] = identifier
                usage = _usage(body.get("usage"))
                evidence["usage_metering"] = "verified" if usage is not None else "unknown"
                evidence["provider_usage_present"] = "usage" in body
                choices = body.get("choices")
                if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
                    return finish("fatal", usage=usage, error="invalid_provider_choices", unknown=True)
                message = choices[0].get("message")
                if not isinstance(message, dict) or message.get("tool_calls") or message.get("function_call"):
                    return finish("fatal", usage=usage, error="provider_tool_call_refused")
                content = message.get("content")
                reason = choices[0].get("finish_reason")
                if reason not in ("stop", "length", "content_filter"):
                    return finish("fatal", usage=usage, error="unknown_provider_finish", unknown=True)
                evidence["finish_reason"] = reason
                evidence["model_outcome"] = {"stop": "completed", "length": "truncated",
                                             "content_filter": "filtered"}[reason]
                if not isinstance(content, str) and not (content is None and reason == "content_filter"):
                    return finish("fatal", usage=usage, error="invalid_assistant_content", unknown=True)
                # 模型拒绝或长度截断是已结束的模型结果，由独立评分器计分；不追加请求。
                return finish("completed", text=content, usage=usage,
                              request_id=evidence["provider_request_id"])
        except TimeoutError:
            return finish("fatal", error="request_deadline_exceeded", unknown=entered)
        except asyncio.CancelledError:
            self.gate.stop()
            return finish("fatal" if entered else "canceled", error="request_canceled",
                          unknown=entered)
        except ImportError:
            return finish("fatal", error="transport_initialization_failure", unknown=entered)
        except httpx.HTTPError:
            return finish("fatal", error="transport_unknown", unknown=entered)
        except (OSError, ValueError, RuntimeError, TypeError):
            return finish("fatal", error="request_boundary_failure", unknown=entered)
        finally:
            # AsyncClient/Response 已完成退出；终点不提前于实际客户端清理。
            if entered and evidence.get("http_returned_at_ns") is None:
                evidence["http_returned_at_ns"] = time.monotonic_ns()
            if reserved:
                with self.gate.lock:
                    self.gate.active.value -= 1
            if acquired:
                self.gate.semaphore.release()
            evidence["ended_at_ns"] = time.monotonic_ns()


def _usage(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    names = ("prompt_tokens", "completion_tokens", "total_tokens")
    if any(type(value.get(name)) is not int or value[name] < 0 for name in names):
        return None
    if value["prompt_tokens"] + value["completion_tokens"] != value["total_tokens"]:
        return None
    result = {name: value[name] for name in names}
    details = value.get("prompt_tokens_details")
    if isinstance(details, dict) and "cached_tokens" in details:
        cached = details["cached_tokens"]
        if type(cached) is not int or not 0 <= cached <= value["prompt_tokens"]:
            return None
        result["cached_tokens"] = cached
    return result
