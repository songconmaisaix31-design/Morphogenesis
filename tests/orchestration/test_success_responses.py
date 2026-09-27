"""Tests to verify that HTTP 200 responses have no classification."""

import json
from unittest.mock import Mock

import httpx
import pytest

from orchestration.provider_adapters.evomap import EvoMapAdapter
from orchestration.provider_adapters.dashscope import DashScopeAdapter
from orchestration.provider_adapters.base import RequestContext


class TestSuccessResponsesNoClassification:
    """Test that successful responses (HTTP 200) have no classification."""

    def test_evomap_200_no_classification(self):
        """Test that EvoMap 200 responses have no classification."""
        # Valid 200 response content
        success_body = json.dumps({
            "id": "cmpl-1234567890",
            "object": "chat.completion",
            "created": 1677825435,
            "model": "gpt-3.5-turbo-0301",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello, how can I help you today?"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20
            }
        })
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(success_body, 200, {}, context)
        
        # For successful responses, classification should be None
        assert result.classification is None
        assert result.normalized_reason is None

    def test_dashscope_200_no_classification(self):
        """Test that DashScope 200 responses have no classification."""
        # Valid 200 response content
        success_body = json.dumps({
            "output": {
                "text": "Hello, how can I help you today?",
                "finish_reason": "stop"
            },
            "usage": {
                "input_tokens": 10,
                "output_tokens": 10,
                "total_tokens": 20
            },
            "request_id": "req-1234567890"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(success_body, 200, {}, context)
        
        # For successful responses, classification should be None
        assert result.classification is None
        assert result.normalized_reason is None

    def test_evomap_non_200_still_classified(self):
        """Test that non-200 EvoMap responses are still properly classified."""
        error_body = json.dumps({
            "error": {
                "code": "InvalidApiKey",
                "message": "Incorrect API key provided"
            }
        })
        context = RequestContext(provider="evomap", model="test-model", endpoint="/chat/completions")
        result = EvoMapAdapter.interpret(error_body, 401, {}, context)
        
        # Non-200 responses should still be classified
        assert result.classification is not None
        assert result.normalized_reason is not None

    def test_dashscope_non_200_still_classified(self):
        """Test that non-200 DashScope responses are still properly classified."""
        error_body = json.dumps({
            "Code": "InvalidApiKey",
            "Message": "Incorrect API key provided"
        })
        context = RequestContext(provider="dashscope", model="test-model", endpoint="/chat/completions")
        result = DashScopeAdapter.interpret(error_body, 401, {}, context)
        
        # Non-200 responses should still be classified
        assert result.classification is not None
        assert result.normalized_reason is not None