"""Tests for provider adapters functionality."""

import json
from datetime import datetime
from unittest.mock import Mock

import pytest

from orchestration.provider_adapters.base import FailureClassification, RequestContext
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
        assert result == FailureClassification.CONFIRMED_REJECTION

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
        assert result == FailureClassification.CONFIRMED_REJECTION

    def test_confirmed_rejection_for_429(self):
        """Test that 429 errors are classified as confirmed rejection."""
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret("", 429, {}, context)
        assert result == FailureClassification.CONFIRMED_REJECTION

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
        assert result == FailureClassification.BUDGET_EXHAUSTED

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
        assert result == FailureClassification.CAPABILITY_MISMATCH

    def test_unknown_effect_for_server_errors(self):
        """Test that server errors are classified as unknown effect."""
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret("", 500, {}, context)
        assert result == FailureClassification.UNKNOWN_EFFECT

    def test_unknown_effect_for_connection_issues(self):
        """Test that connection errors are classified as unknown effect."""
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret("", 0, {}, context)
        assert result == FailureClassification.UNKNOWN_EFFECT


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
        assert result == FailureClassification.CONFIRMED_REJECTION

    def test_confirmed_rejection_for_allocation_quota_free_tier_dashscope(self):
        """Test that DashScope free tier allocation errors are classified as confirmed rejection."""
        error_body = json.dumps({
            "Code": "AllocationQuota.FreeTierOnly",
            "Message": "Free tier only"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 403, {}, context)
        assert result == FailureClassification.CONFIRMED_REJECTION

    def test_confirmed_rejection_for_429_dashscope(self):
        """Test that DashScope 429 errors are classified as confirmed rejection."""
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret("", 429, {}, context)
        assert result == FailureClassification.CONFIRMED_REJECTION

    def test_budget_exhausted_for_insufficient_balance_dashscope(self):
        """Test that DashScope insufficient balance errors are classified as budget exhausted."""
        error_body = json.dumps({
            "Code": "InvalidArgument",
            "Message": "Insufficient balance in account"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 400, {}, context)
        assert result == FailureClassification.BUDGET_EXHAUSTED

    def test_capability_mismatch_for_model_not_found_dashscope(self):
        """Test that DashScope model not found errors are classified as capability mismatch."""
        error_body = json.dumps({
            "Code": "ModelNotImplemented",
            "Message": "Requested model is not available"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 400, {}, context)
        assert result == FailureClassification.CAPABILITY_MISMATCH

    def test_unknown_effect_for_server_errors_dashscope(self):
        """Test that DashScope server errors are classified as unknown effect."""
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret("", 500, {}, context)
        assert result == FailureClassification.UNKNOWN_EFFECT