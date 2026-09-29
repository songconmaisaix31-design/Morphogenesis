"""Status/transport authority must survive misleading provider error text."""
import json

import pytest

from orchestration.provider_adapters.base import FailureClassification, RequestContext
from orchestration.provider_adapters.dashscope import DashScopeAdapter
from orchestration.provider_adapters.evomap import EvoMapAdapter


ERRORS = [
    ("Arrearage", "Account has outstanding balance"),
    ("Arrearage", "账户欠费，余额不足"),
    ("AllocationQuota.FreeTierOnly", "Free tier quota exceeded"),
    ("AllocationQuota.FreeTierOnly", "免费配额已耗尽"),
    ("InsufficientFunds", "insufficient funds; insufficient balance; account balance"),
    ("GatewayError", "payment required; billing; quota exceeded"),
    ("GatewayError", "账户余额不足，配额已用完，请充值"),
    ("ModelNotFound", "model not found; unsupported; not available"),
]


def error_body(provider, code, message):
    if provider == "dashscope":
        return json.dumps({"Code": code, "Message": message}, ensure_ascii=False)
    return json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False)


@pytest.mark.parametrize("provider,adapter", [("dashscope", DashScopeAdapter), ("evomap", EvoMapAdapter)])
@pytest.mark.parametrize("status", [0, 500, 502, 503, 504])
@pytest.mark.parametrize("code,message", ERRORS)
def test_unknown_status_precedes_provider_body(provider, adapter, status, code, message):
    context = RequestContext(provider=provider, model="fixture", endpoint="/chat/completions")
    result = adapter.interpret(error_body(provider, code, message), status, {"Retry-After": "17"}, context)

    assert result.classification == FailureClassification.UNKNOWN_EFFECT
    assert result.normalized_reason == ("connection_failure" if status == 0 else f"http_{status}")
    assert result.retry_after_raw == "17" and result.retry_after_seconds == 17.0


@pytest.mark.parametrize("adapter", [DashScopeAdapter, EvoMapAdapter])
@pytest.mark.parametrize("body", ["账户欠费 quota exceeded account balance", "null", "[]", '{"message":"billing"}'])
def test_server_error_does_not_require_a_provider_json_shape(adapter, body):
    context = RequestContext(provider="fixture", model="fixture", endpoint="/chat/completions")
    result = adapter.interpret(body, 503, {}, context)
    assert result.classification == FailureClassification.UNKNOWN_EFFECT
    assert result.normalized_reason == "http_503"


@pytest.mark.parametrize("provider,adapter", [("dashscope", DashScopeAdapter), ("evomap", EvoMapAdapter)])
@pytest.mark.parametrize("status,code,message,expected", [
    (400, "Arrearage", "账户欠费", FailureClassification.CONFIRMED_REJECTION),
    (403, "AllocationQuota.FreeTierOnly", "配额耗尽", FailureClassification.CONFIRMED_REJECTION),
    (429, "RateLimit", "too many requests", FailureClassification.CONFIRMED_REJECTION),
    (400, "InvalidArgument", "bad request", FailureClassification.CONFIRMED_REJECTION),
    (402, "Payment", "payment required", FailureClassification.BUDGET_EXHAUSTED),
    (404, "ModelNotFound", "model not found", FailureClassification.CAPABILITY_MISMATCH),
])
def test_existing_client_error_contract_is_preserved(provider, adapter, status, code, message, expected):
    context = RequestContext(provider=provider, model="fixture", endpoint="/chat/completions")
    result = adapter.interpret(error_body(provider, code, message), status, {}, context)
    assert result.classification == expected


@pytest.mark.parametrize("adapter", [DashScopeAdapter, EvoMapAdapter])
def test_plain_client_error_and_success_controls(adapter):
    context = RequestContext(provider="fixture", model="fixture", endpoint="/chat/completions")
    rejected = adapter.interpret("bad request", 400, {}, context)
    success = adapter.interpret('{"message":"billing"}', 200, {}, context)
    assert rejected.classification == FailureClassification.CONFIRMED_REJECTION
    assert success.classification is success.normalized_reason is None
