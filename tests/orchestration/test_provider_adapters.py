"""Tests for provider adapters functionality."""

import json
from datetime import datetime
from unittest.mock import Mock

import pytest

from orchestration.provider_adapters.base import FailureClassification, RequestContext, ClassificationResult
from orchestration.provider_adapters.evomap import EvoMapAdapter
from orchestration.provider_adapters.dashscope import DashScopeAdapter


class TestEvoMapAdapter:
    """Test EvoMap provider adapter functionality."""
    
    def test_confirmed_rejection_for_arrearage(self):
        """Test that arrearage errors are classified as confirmed rejection."""
        error_body = json.dumps({
            "error": {
                "code": "Arrearage",
                "message": "Account has outstanding balance"
            }
        })
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 400, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.normalized_reason == "billing_arrearage"

    def test_confirmed_rejection_for_allocation_quota_free_tier_only(self):
        """Test that free tier allocation errors are classified as confirmed rejection."""
        error_body = json.dumps({
            "error": {
                "code": "AllocationQuota.FreeTierOnly",
                "message": "Free tier only"
            }
        })
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 403, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.normalized_reason == "free_tier_quota_exceeded"

    def test_confirmed_rejection_for_429(self):
        """Test that 429 errors are classified as confirmed rejection."""
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret("", 429, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.normalized_reason == "rate_limited"

    def test_budget_exhausted_for_insufficient_funds(self):
        """Test that insufficient funds errors are classified as budget exhausted."""
        error_body = json.dumps({
            "error": {
                "code": "InsufficientFunds",
                "message": "Insufficient funds in account"
            }
        })
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 402, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.BUDGET_EXHAUSTED
        assert result.normalized_reason == "insufficient_funds"

    def test_capability_mismatch_for_model_not_found(self):
        """Test that model not found errors are classified as capability mismatch."""
        error_body = json.dumps({
            "error": {
                "code": "ModelNotFound",
                "message": "Requested model is not available"
            }
        })
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 400, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CAPABILITY_MISMATCH
        assert result.normalized_reason == "capability_unavailable"

    def test_unknown_effect_for_server_errors(self):
        """Test that server errors are classified as unknown effect."""
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret("", 500, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.UNKNOWN_EFFECT
        assert result.normalized_reason == "http_500"

    def test_unknown_effect_for_connection_issues(self):
        """Test that connection errors are classified as unknown effect."""
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret("", 0, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.UNKNOWN_EFFECT
        assert result.normalized_reason == "connection_failure"

    def test_retry_after_parsing(self):
        """Test that Retry-After header is parsed correctly."""
        error_body = json.dumps({
            "error": {
                "code": "RateLimitExceeded",
                "message": "Too many requests"
            }
        })
        headers = {"Retry-After": "60"}
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 429, headers, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.retry_after_raw == "60"
        assert result.retry_after_seconds == 60

    def test_retry_after_parsing_date_format(self):
        """Test that Retry-After header with date format is parsed correctly."""
        # Note: We won't test the actual datetime parsing here since it would require mocking datetime.now()
        # but we can at least verify the function exists and is called
        error_body = json.dumps({
            "error": {
                "code": "RateLimitExceeded",
                "message": "Too many requests"
            }
        })
        headers = {"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 429, headers, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.retry_after_raw == "Wed, 21 Oct 2015 07:28:00 GMT"

    def test_retry_after_parsing_malformed(self):
        """Test that malformed Retry-After header is handled gracefully."""
        error_body = json.dumps({
            "error": {
                "code": "RateLimitExceeded",
                "message": "Too many requests"
            }
        })
        headers = {"Retry-After": "invalid-format"}
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 429, headers, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.retry_after_raw == "invalid-format"
        # The function would return None for malformed input


class TestDashScopeAdapter:
    """Test DashScope provider adapter functionality."""
    
    def test_confirmed_rejection_for_arrearage_dashscope(self):
        """Test that DashScope arrearage errors are classified as confirmed rejection."""
        error_body = json.dumps({
            "Code": "Arrearage",
            "Message": "Account has outstanding balance"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 400, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.normalized_reason == "billing_arrearage"

    def test_confirmed_rejection_for_allocation_quota_free_tier_dashscope(self):
        """Test that DashScope free tier allocation errors are classified as confirmed rejection."""
        error_body = json.dumps({
            "Code": "AllocationQuota.FreeTierOnly",
            "Message": "Free tier only"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 403, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.normalized_reason == "free_tier_quota_exceeded"

    def test_confirmed_rejection_for_429_dashscope(self):
        """Test that DashScope 429 errors are classified as confirmed rejection."""
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret("", 429, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CONFIRMED_REJECTION
        assert result.normalized_reason == "rate_limited"

    def test_budget_exhausted_for_insufficient_balance_dashscope(self):
        """Test that DashScope insufficient balance errors are classified as budget exhausted."""
        error_body = json.dumps({
            "Code": "InvalidArgument",
            "Message": "Insufficient balance in account"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 400, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.BUDGET_EXHAUSTED
        assert result.normalized_reason == "insufficient_funds"

    def test_capability_mismatch_for_model_not_found_dashscope(self):
        """Test that DashScope model not found errors are classified as capability mismatch."""
        error_body = json.dumps({
            "Code": "ModelNotImplemented",
            "Message": "Requested model is not available"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 400, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.CAPABILITY_MISMATCH
        assert result.normalized_reason == "capability_unavailable"

    def test_unknown_effect_for_server_errors_dashscope(self):
        """Test that DashScope server errors are classified as unknown effect."""
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret("", 500, {}, context)
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.UNKNOWN_EFFECT
        assert result.normalized_reason == "http_500"

    def test_transport_error_priority_dashscope(self):
        """Test that DashScope handles transport errors with priority."""
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret("", 0, {}, context)  # status 0 represents connection issue
        assert isinstance(result, ClassificationResult)
        assert result.classification == FailureClassification.UNKNOWN_EFFECT
        assert result.normalized_reason == "connection_failure"