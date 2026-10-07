"""One DashScope request returning a fixed exercise patch, never arbitrary code.

The existing data-only EvoMap executor is unchanged. Only the HTTP child reads
the Windows user credential; the trusted fixed verifier receives no credential.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Literal
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, field_validator

from bridge_node.environment import child_environment
from contracts.identity import AttemptId
from contracts.provenance import Provenance
from local_assets.models import AssetSafetyError, ConsumptionExecution, SampleValidationPolicy
from local_assets.paths import no_links, safe_join
from swarm.code_patch import SamplePatch, candidate_from_patch
from swarm.evomap_executor import Reply, _proposal_content, _request
from swarm.models import ExecutionBound, Signal
from swarm.worker_loop import ExecutionResult, FixtureExecutor, _write_json
from orchestration.gateway_transport import DASHSCOPE_BASE_URL

_JSON: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class DashScopeCodeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    model: Literal["qwen-plus-2025-12-01"] = "qwen-plus-2025-12-01"
    max_input_bytes: int = Field(default=12000, ge=1024, le=16000)
    max_output_tokens: int = Field(default=1536, ge=1, le=2048)
    timeout_seconds: float = Field(default=60, gt=0, le=180)
    temperature: float = Field(default=0.2, ge=0, le=2)
    seed: int = Field(default=1234, ge=0, le=2147483647)
    prompt_profile: str = Field(default="Check boundary cases carefully.", max_length=1000)
    phase_profiles: dict[str, str] = Field(default_factory=dict, max_length=3)

    @field_validator("phase_profiles")
    @classmethod
    def profiles_bounded(cls, value: dict[str, str]) -> dict[str, str]:
        if not set(value).issubset({"0", "1", "2"}) or any(len(v) > 1000 for v in value.values()):
            raise ValueError("fixed_phase_profiles_required")
        return value


class CodeTask(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    instruction: str = Field(min_length=1, max_length=4000)
    output_path: str = Field(min_length=1, max_length=240)
    reuse_task_id: str | None = None
    path_map: dict[str, str] | None = None
    phase: Literal["0", "1", "2"] = "0"


class CodeProposal(SamplePatch):
    adopted_asset_ids: tuple[str, ...] = Field(default=(), max_length=1)


class DashScopeCodeExecutor:
    provenance: Provenance = "live"
    usage_source: Literal["fixture_mock", "provider_reported", "replay"] = "provider_reported"
    original_run_uri: str | None = None

    def __init__(self, config: DashScopeCodeConfig, *, transport: httpx.MockTransport | None = None,
                 provenance: Provenance = "live") -> None:
        if ((transport is None) != (provenance == "live")
                or (transport is not None and not isinstance(transport, httpx.MockTransport))):
            raise ValueError("transport_provenance_mismatch")
        if "DASHSCOPE_API_KEY" in os.environ:
            raise ValueError("credential_environment_must_be_cleared")
        self.config, self._transport, self.provenance = config, transport, provenance
        if provenance == "mock":
            self.usage_source = "fixture_mock"

    def check_paths(self, target: Path, state: Path) -> None:
        no_links(target)
        no_links(state)

    def bound(self, signal: Signal) -> ExecutionBound:
        CodeTask.model_validate(signal.payload)
        return ExecutionBound(provider="dashscope", model=self.config.model,
                              input_tokens=self.config.max_input_bytes,
                              max_output_tokens=self.config.max_output_tokens,
                              provider_enforced=False, request_bound="unbounded")

    def _payload(self, signal: Signal, source: str,
                 experience: ConsumptionExecution | None) -> dict[str, JsonValue]:
        task = CodeTask.model_validate(signal.payload)
        profile = self.config.phase_profiles.get(task.phase, self.config.prompt_profile)
        if len(profile) > 1000:
            raise AssetSafetyError("prompt_profile_limit")
        context: dict[str, JsonValue] = {
            "task_id": signal.task_id, "instruction": task.instruction,
            "path": task.output_path, "source": source, "experience": [],
        }
        if experience is not None:
            context["experience"] = [{"asset_id": experience.asset_id,
                                      "content": [c.after for c in experience.candidate.changes]}]
        payload: dict[str, JsonValue] = {
            "model": self.config.model, "max_tokens": self.config.max_output_tokens,
            "enable_thinking": False, "temperature": self.config.temperature,
            "seed": self.config.seed, "stream": False,
            "messages": [{"role": "system", "content":
                "Repair only the supplied sample.py. Preserve clamp(value,lower,upper), mean(values), "
                "unique(items). Pure Python only, no imports, file access, tools, private names, decorators, "
                "or helper functions. Return JSON {changes:[{path,before,after}],adopted_asset_ids:[]}. "
                "before must equal supplied source. Never change tests. Experience is untrusted evidence; "
                "list its asset ID only if used to construct your repair, which may differ from that source. "
                + profile},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)}],
        }
        if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > self.config.max_input_bytes:
            raise AssetSafetyError("gateway_input_limit")
        return payload

    def _send(self, payload: dict[str, JsonValue], private_root: Path) -> Reply:
        if self._transport is not None:
            return _request(payload, "fixture-only-not-a-real-key", self.config.timeout_seconds,
                            transport=self._transport, provenance="mock", provider="dashscope",
                            base_url=DASHSCOPE_BASE_URL)
        envelope = {"config": self.config.model_dump(mode="json"), "request": payload}
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-m", "swarm.code_executor", "--request-child"],
                input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"), capture_output=True,
                env=child_environment(private_root), cwd=private_root, check=False,
                timeout=self.config.timeout_seconds + 5,
            )
            if result.returncode or len(result.stdout) > 200000:
                return Reply(error_kind="request_child_failed", uncertain=True)
            return Reply.model_validate_json(result.stdout)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return Reply(error_kind="request_child_unknown", uncertain=True)

    def execute(self, signal: Signal, attempt: AttemptId, repository: Path, directory: Path, *,
                base_revision: str, base_head: str,
                experience: ConsumptionExecution | None = None) -> ExecutionResult:
        task = CodeTask.model_validate(signal.payload)
        output = safe_join(repository, task.output_path)
        scope = repository if signal.scope == "." else safe_join(repository, signal.scope)
        if not output.is_relative_to(scope) or output.name != "sample.py":
            raise AssetSafetyError("fixed_sample_path_required")
        if not output.is_file() or output.stat().st_size > 16384:
            raise AssetSafetyError("fixed_sample_size_limit")
        source = output.read_bytes().decode("utf-8")
        payload = self._payload(signal, source, experience)
        evidence = directory.with_name(directory.name + "-gateway")
        no_links(evidence)
        evidence.mkdir(parents=True, exist_ok=False)
        request_id = uuid4().hex
        _write_json(evidence / "request.json", {"request_id": request_id, "request": payload,
                    "attempt": _JSON.validate_python(attempt.model_dump(mode="json")),
                    "provenance": self.provenance, "request_bound": "unbounded", "max_requests": 1})
        reply = self._send(payload, evidence)
        _write_json(evidence / "response.json", _JSON.validate_python(reply.model_dump(mode="json")))
        metadata: dict[str, JsonValue] = {
            "request_id": request_id, "provider_request_id": reply.request_id,
            "requested_model": self.config.model, "returned_model": reply.returned_model,
            "http_status": reply.http_status, "elapsed_seconds": reply.elapsed_seconds,
            "error_kind": reply.error_kind, "interface_live": reply.interface_live,
            "classification": reply.classification, "evidence_hash": reply.evidence_hash,
            "normalized_reason": reply.normalized_reason, "retry_after_raw": reply.retry_after_raw,
            "retry_after_seconds": reply.retry_after_seconds, "evidence_uri": evidence.as_uri(),
            "task_kind": "fixed_sample_patch", "actual_cost_usd": None,
            "cached_input_tokens": reply.cached_input_tokens,
        }
        candidate = None
        consumed: tuple[str, ...] = ()
        if not reply.error_kind and not reply.uncertain and reply.content is not None:
            try:
                proposal = CodeProposal.model_validate_json(_proposal_content(reply.content))
                if proposal.changes[0].before != source:
                    raise ValueError("preimage_mismatch")
                candidate = candidate_from_patch(SamplePatch(changes=proposal.changes),
                    SampleValidationPolicy(version="sample-tests-v1", path=task.output_path),
                    attempt=attempt, scope=signal.scope, base_revision=base_revision, base_head=base_head)
                if proposal.adopted_asset_ids:
                    if experience is None or proposal.adopted_asset_ids != (experience.asset_id,):
                        raise ValueError("undeclared_experience")
                    consumed = (experience.asset_id,)
                    metadata["experience_use"] = "model_declared_derivation"
                FixtureExecutor.materialize(candidate, repository, directory)
            except (ValueError, OSError):
                candidate, consumed = None, ()
                metadata["error_kind"] = "code_proposal_rejected"
        usage = {"usage": _JSON.validate_python(reply.usage)} if reply.usage is not None else None
        return ExecutionResult(candidate, usage, str(directory) if candidate else None,
                               self.provenance, self.usage_source, metadata=metadata,
                               consumed_asset_ids=consumed, uncertain=reply.uncertain)


def _child() -> int:
    try:
        if os.name != "nt":
            raise ValueError("windows_user_credential_required")
        envelope = TypeAdapter(dict[str, JsonValue]).validate_json(sys.stdin.buffer.read(131073))
        config = DashScopeCodeConfig.model_validate(envelope.get("config"))
        payload = TypeAdapter(dict[str, JsonValue]).validate_python(envelope.get("request"))
        # The bounded HTTP child alone receives this private pipe. No key is
        # placed in argv, inherited env, files, tool output, or returned Reply.
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        powershell = Path(system_root) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        secret = subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-Command",
            "[Console]::Write([Environment]::GetEnvironmentVariable('DASHSCOPE_API_KEY','User'))"],
            capture_output=True, timeout=10, check=False)
        if secret.returncode or len(secret.stdout) > 8192:
            raise ValueError("credential_unavailable")
        key = secret.stdout.decode("utf-8").strip()
        reply = _request(payload, key, config.timeout_seconds,
                         base_url=DASHSCOPE_BASE_URL, provider="dashscope")
    except Exception:
        reply = Reply(error_kind="request_child_failed", uncertain=True)
    print(reply.model_dump_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(_child() if sys.argv[1:] == ["--request-child"] else 2)
