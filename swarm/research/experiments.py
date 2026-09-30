"""Thin bridge to C's sole experiment contracts and trusted archive reader."""
from __future__ import annotations

import asyncio
import importlib
import os
from pathlib import Path
from typing import Any

from pydantic import JsonValue, TypeAdapter

from local_assets.models import AssetSafetyError
from local_assets.paths import no_links
from swarm.models import Lease
from swarm.research.models import HostConfig

_OBJECT = TypeAdapter(dict[str, JsonValue])


class OfficialExperiments:
    def __init__(self, config: HostConfig) -> None:
        self.root = Path(config.evidence_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.models = importlib.import_module("orchestration.experiments.models")
        self.module = importlib.import_module("orchestration.experiments.executor")
        backend = importlib.import_module("orchestration.experiments.backend")
        settings = config.experiment_backend
        unknown = set(settings) - {"domain", "protocol", "api_key_env", "use_server_proxy", "codeinterpreter", "notebook", "volumes"}
        if unknown or settings.get("protocol", "http") not in {"http", "https"}:
            raise ValueError("unsupported_experiment_host_settings")
        def enabled(name: str, default: str = "false") -> bool:
            value = settings.get(name, default)
            if value not in {"true", "false"}:
                raise ValueError("experiment_boolean_settings_require_true_false")
            return value == "true"
        secret = os.environ.get(settings["api_key_env"]) if settings.get("api_key_env") else None
        if settings.get("api_key_env") and not secret:
            raise ValueError("experiment_host_api_key_environment_missing")
        self.executor: Any = self.module.ExperimentExecutor(backend.OpenSandboxBackend(
            domain=settings.get("domain", "127.0.0.1:8097"), protocol=settings.get("protocol", "http"),
            api_key=secret, use_server_proxy=enabled("use_server_proxy", "true"),
            codeinterpreter=enabled("codeinterpreter"), notebook=enabled("notebook"), volumes=enabled("volumes")))

    def _context(self, run_id: str, lease: Lease) -> Any:
        return self.models.ExperimentContext(run_id=run_id, task_id=lease.task_id,
                                             worker_id=lease.worker_id, fencing_token=lease.token)

    @staticmethod
    def _flat(result: Any) -> dict[str, JsonValue]:
        scientific = result.scientific
        return {"execution_state": str(result.execution_state), "scientific_verdict": str(scientific.verdict),
                "effect_state": str(result.remote_effect), "sandbox_id": result.sandbox_id,
                "provenance": str(result.provenance), "reasons": list(result.reasons) + list(scientific.reasons),
                "exit_code": result.exit_code, "usage": None, "cost_usd": None,
                "experiment_result": _OBJECT.validate_json(result.model_dump_json())}

    async def execute(self, plan: dict[str, JsonValue], run_id: str, lease: Lease) -> dict[str, JsonValue]:
        registered = self.models.ExperimentPlan.model_validate(plan)
        result = await asyncio.to_thread(self.executor.execute, registered, self._context(run_id, lease), self.root)
        return self._flat(result)

    def read(self, run_id: str) -> dict[str, JsonValue]:
        no_links(self.root / run_id)
        result = self.module.read_result(self.root, run_id)
        return self._flat(result)

    def evaluate(self, run_id: str, plan: dict[str, JsonValue], lease: Lease) -> dict[str, JsonValue]:
        registered = self.models.ExperimentPlan.model_validate(plan)
        no_links(self.root / run_id)
        result = self.module.read_result(self.root, run_id, expected_plan=registered,
                                         expected_context=self._context(run_id, lease))
        output = self._flat(result)
        code = self.root / run_id / "inputs" / registered.code.name
        if not code.is_file():
            output["code_text"] = None
            if result.execution_state == "succeeded":
                raise AssetSafetyError("missing_executed_code_evidence")
        else:
            no_links(code)
            output["code_text"] = code.read_bytes().decode("utf-8")
        return output
