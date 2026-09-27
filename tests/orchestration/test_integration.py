"""Integration tests for the failure classification functionality."""

import hashlib
import json
from unittest.mock import Mock

import httpx
import pytest

from orchestration.gateway_transport import single_request
from swarm.evomap_executor import _request, Reply


def test_request_classification_integration():
    """Test that the _request function properly classifies responses and generates evidence hash."""
    # Create a mock transport that returns a response with a specific error
    def mock_handler(request):
        return httpx.Response(
            status_code=400,
            headers={"x-request-id": "test-id"},
            content=b'{"error": {"code": "Arrearage", "message": "Account has outstanding balance"}}'
        )
    
    transport = httpx.MockTransport(mock_handler)
    
    # Make a request using the _request function
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    reply = _request(payload, "test-key", 30, transport=transport, provenance="mock")
    
    # Verify that the reply contains the expected fields
    assert isinstance(reply, Reply)
    assert reply.classification is not None
    assert reply.evidence_hash is not None
    assert reply.http_status == 400
    assert reply.request_id == "test-id"
    
    # Verify that the classification is correct for arrearage
    assert reply.classification == "confirmed_rejection"
    
    # Verify that evidence hash corresponds to the raw body
    expected_hash = hashlib.sha256(b'{"error": {"code": "Arrearage", "message": "Account has outstanding balance"}}').hexdigest()
    assert reply.evidence_hash == expected_hash


def test_request_429_classification():
    """Test that 429 errors are properly classified."""
    def mock_handler(request):
        return httpx.Response(
            status_code=429,
            headers={"Retry-After": "60", "x-request-id": "rate-limited-id"},
            content=b'{"error": {"code": "RateLimitExceeded", "message": "Too many requests"}}'
        )
    
    transport = httpx.MockTransport(mock_handler)
    
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    reply = _request(payload, "test-key", 30, transport=transport, provenance="mock")
    
    assert reply.http_status == 429
    assert reply.classification == "confirmed_rejection"
    assert reply.evidence_hash is not None


def test_request_unknown_effect_classification():
    """Test that server errors are classified as unknown effect."""
    def mock_handler(request):
        return httpx.Response(
            status_code=500,
            headers={"x-request-id": "server-error-id"},
            content=b'{"error": {"code": "InternalServerError", "message": "Something went wrong"}}'
        )
    
    transport = httpx.MockTransport(mock_handler)
    
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    reply = _request(payload, "test-key", 30, transport=transport, provenance="mock")
    
    assert reply.http_status == 500
    assert reply.classification == "unknown_effect"
    assert reply.evidence_hash is not None