"""Tests for gateway transport functionality."""

import json
from unittest.mock import Mock

import httpx
import pytest

from orchestration.gateway_transport import single_request, GatewayResponse, EVOMAP_BASE_URL


def test_gateway_response_includes_retry_after_and_raw_body():
    """Test that GatewayResponse includes retry_after and raw_body fields."""
    # Create a mock transport that returns a response with Retry-After header
    def mock_handler(request):
        return httpx.Response(
            status_code=429,
            headers={"Retry-After": "30", "x-request-id": "test-id"},
            content=b'{"error": {"code": "rate_limited", "message": "Too many requests"}}'
        )
    
    transport = httpx.MockTransport(mock_handler)
    
    # Make a request with the mock transport
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    response = single_request(payload, key="test-key", phase_timeout=30, transport=transport)
    
    # Verify that the response includes the new fields
    assert isinstance(response, GatewayResponse)
    assert response.retry_after == "30"
    assert response.raw_body is not None
    assert b"rate_limited" in response.raw_body


def test_gateway_response_without_retry_after():
    """Test that GatewayResponse handles missing Retry-After header."""
    # Create a mock transport that returns a response without Retry-After header
    def mock_handler(request):
        return httpx.Response(
            status_code=200,
            headers={"x-request-id": "test-id"},
            content=b'{"choices": [{"message": {"content": "Hello"}}]}'
        )
    
    transport = httpx.MockTransport(mock_handler)
    
    # Make a request with the mock transport
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    response = single_request(payload, key="test-key", phase_timeout=30, transport=transport)
    
    # Verify that the response handles missing Retry-After correctly
    assert isinstance(response, GatewayResponse)
    assert response.retry_after is None
    assert response.raw_body is not None


def test_gateway_response_with_various_status_codes():
    """Test GatewayResponse with different status codes."""
    def mock_handler(request):
        return httpx.Response(
            status_code=400,
            headers={"Retry-After": "60"},
            content=b'{"error": {"code": "Arrearage", "message": "Account has outstanding balance"}}'
        )
    
    transport = httpx.MockTransport(mock_handler)
    
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    response = single_request(payload, key="test-key", phase_timeout=30, transport=transport)
    
    assert response.status == 400
    assert response.retry_after == "60"
    assert response.raw_body is not None