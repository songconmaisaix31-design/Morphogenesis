"""Integration tests for the failure classification functionality."""

import hashlib
import json
import subprocess
import sys
from unittest.mock import Mock

import httpx
import pytest

from orchestration.gateway_transport import single_request
from swarm.evomap_executor import _request, Reply, EvoMapConfig
from pydantic import TypeAdapter
from pydantic import JsonValue


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


def test_transport_error_priority():
    """Test that transport errors take precedence over status/body classification."""
    def mock_handler(request):
        # Simulate a transport error by raising an exception
        raise httpx.ReadTimeout("Read timed out")
    
    transport = httpx.MockTransport(mock_handler)
    
    payload = {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    reply = _request(payload, "test-key", 30, transport=transport, provenance="mock")
    
    # Transport errors should result in unknown_effect regardless of status code
    assert reply.classification == "unknown_effect"
    assert reply.error_kind is not None
    assert reply.uncertain is True


def test_subprocess_integration():
    """Test the subprocess integration for --request-child with mock data."""
    # Create a mock credential file
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cred_file:
        cred_file.write("test-key")
        cred_file.flush()

        # Prepare the request envelope with mock data
        payload = {"model": "evomap-gpt-5.6-luna", "messages": [{"role": "user", "content": "Hello"}]}
        config = EvoMapConfig(
            model="evomap-gpt-5.6-luna",
            credential_file=cred_file.name
        )
        # Use the new mock_spec flag to indicate this is a mock request for the subprocess
        envelope = {"config": config.model_dump(mode="json"), "request": payload, "mock_spec": "400_arrearage"}

        # Execute the subprocess with --request-child
        result = subprocess.run([
            sys.executable, "-m", "swarm.evomap_executor", "--request-child"
        ],
        input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env={**os.environ, "PYTHONPATH": os.getcwd()}
        )

        # Clean up the file
        try:
            os.unlink(cred_file.name)
        except (PermissionError, OSError):
            # File may still be locked by subprocess, ignore on Windows
            pass

        # Check that the subprocess executed successfully
        assert result.returncode == 0

        # Parse the output to ensure it contains classification and evidence_hash
        output = result.stdout.decode('utf-8')
        reply_data = TypeAdapter(dict[str, JsonValue]).validate_json(output)

        # Verify that the response contains the expected fields
        assert 'classification' in reply_data
        assert 'evidence_hash' in reply_data
        # Also verify the new fields are present
        assert 'normalized_reason' in reply_data
        assert 'retry_after_raw' in reply_data
        assert 'retry_after_seconds' in reply_data

        # Verify that no raw body or key information is leaked
        assert reply_data.get('interface_live') == 'not_run'  # Should be mock
        # Verify specific values for the arrearage case
        assert reply_data['classification'] == 'confirmed_rejection'
        assert reply_data['normalized_reason'] == 'billing_arrearage'


@pytest.mark.parametrize("mock_spec,expected_classification,expected_reason", [
    ("400_arrearage", "confirmed_rejection", "billing_arrearage"),
    ("403_freetier", "confirmed_rejection", "free_tier_quota_exceeded"),
    ("429_with_retry_after", "confirmed_rejection", "rate_limited"),
    ("drop_mid_response", "unknown_effect", "ReadTimeout"),
])
def test_subprocess_scenarios(mock_spec, expected_classification, expected_reason):
    """Test various subprocess scenarios with different error types."""
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as cred_file:
        cred_file.write("test-key")
        cred_file.flush()

        # Prepare the request envelope with mock data
        payload = {"model": "evomap-gpt-5.6-luna", "messages": [{"role": "user", "content": "Hello"}]}
        config = EvoMapConfig(
            model="evomap-gpt-5.6-luna",
            credential_file=cred_file.name
        )
        # Use different mock specs for different scenarios
        envelope = {"config": config.model_dump(mode="json"), "request": payload, "mock_spec": mock_spec}

        # Execute the subprocess with --request-child
        result = subprocess.run([
            sys.executable, "-m", "swarm.evomap_executor", "--request-child"
        ],
        input=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        env={**os.environ, "PYTHONPATH": os.getcwd()}
        )

        # Clean up the file
        try:
            os.unlink(cred_file.name)
        except (PermissionError, OSError):
            # File may still be locked by subprocess, ignore on Windows
            pass

        # Check that the subprocess executed (may return non-zero for errors)
        assert result.returncode == 0, f"Subprocess failed with stderr: {result.stderr}"

        # Parse the output
        output = result.stdout.decode('utf-8')
        reply_data = TypeAdapter(dict[str, JsonValue]).validate_json(output)

        # Verify that the response contains the expected fields
        assert 'classification' in reply_data
        assert 'evidence_hash' in reply_data
        assert 'normalized_reason' in reply_data
        assert 'retry_after_raw' in reply_data
        assert 'retry_after_seconds' in reply_data

        # Verify classification and reason match expectations
        assert reply_data['classification'] == expected_classification
        if mock_spec == "drop_mid_response":
            # For transport errors, check that error_kind contains the expected error
            assert expected_reason in (reply_data.get('error_kind') or "")
        else:
            assert reply_data['normalized_reason'] == expected_reason

        # For 429 case, verify retry_after fields are populated
        if mock_spec == "429_with_retry_after":
            assert reply_data['retry_after_raw'] == "120"
            assert reply_data['retry_after_seconds'] == 120.0

        # Verify that no credential information is leaked in stdout/stderr
        assert "test-key" not in output
        assert "test-key" not in result.stderr.decode('utf-8')