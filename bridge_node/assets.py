"""Official Node GEP SDK via one JSON request per shell-free child process."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue, TypeAdapter, ValidationError

from bridge_node.environment import child_environment


class BridgeError(RuntimeError):
    """Sanitized bridge failure; raw child stdout/stderr are never attached."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class SchemaIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    keyword: str


class AssetValidation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    valid: bool
    schema_valid: bool
    asset_id_valid: bool
    schema_version: Literal["1.14.0"]
    errors: list[SchemaIssue]


class _Response(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ok: bool
    result: JsonValue = None
    error: str | None = None


class NodeAssetBridge:
    """No Python hash fallback: an unavailable official SDK fails closed."""

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be finite and positive")
        self.timeout_seconds = timeout_seconds
        self._script = Path(__file__).with_name("asset_bridge.mjs")

    def _invoke(self, operation: str, value: JsonValue) -> JsonValue:
        executable = shutil.which("node")
        if executable is None:
            raise BridgeError("node_unavailable")
        try:
            request = json.dumps(
                {"operation": operation, "value": value},
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8")
        except (ValueError, TypeError, UnicodeError):
            raise BridgeError("invalid_json_value") from None
        if len(request) > 2 * 1024 * 1024:
            raise BridgeError("request_too_large")
        with tempfile.TemporaryDirectory(prefix="morph-sdk-") as directory:
            workspace = Path(directory)
            try:
                completed = subprocess.run(
                    [executable, str(self._script)], input=request,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=self.timeout_seconds, check=False, shell=False,
                    cwd=workspace, env=child_environment(workspace),
                )
            except subprocess.TimeoutExpired:
                # subprocess.run kills AND waits for the child on timeout.
                raise BridgeError("sdk_timeout") from None
            except OSError:
                raise BridgeError("sdk_start_failed") from None
        try:
            response = _Response.model_validate_json(completed.stdout)
        except (ValidationError, ValueError):
            code = "sdk_process_failed" if completed.returncode else "sdk_invalid_response"
            raise BridgeError(code) from None
        if completed.returncode != 0 or not response.ok:
            known = {
                "unsupported_asset_type", "request_too_large", "invalid_json",
                "sdk_version_mismatch", "invalid_request", "unsupported_operation", "sdk_error",
            }
            code = response.error if response.error in known else "sdk_process_failed"
            raise BridgeError(code or "sdk_process_failed")
        return response.result

    def canonicalize(self, value: JsonValue) -> str:
        return self._typed("canonicalize", value, str)

    def compute_asset_id(self, asset: dict[str, JsonValue]) -> str:
        return self._typed("computeAssetId", asset, str)

    def verify_asset_id(self, asset: dict[str, JsonValue]) -> bool:
        return self._typed("verifyAssetId", asset, bool)

    def validate_asset(self, asset: dict[str, JsonValue]) -> AssetValidation:
        try:
            return AssetValidation.model_validate(self._invoke("validateAsset", asset))
        except ValidationError:
            raise BridgeError("sdk_invalid_response") from None

    def _typed[T](self, operation: str, value: JsonValue, result_type: type[T]) -> T:
        try:
            return TypeAdapter(result_type).validate_python(self._invoke(operation, value), strict=True)
        except ValidationError:
            raise BridgeError("sdk_invalid_response") from None
