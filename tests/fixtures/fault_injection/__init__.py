"""Fault injection fixtures for testing failure chain behaviors"""

import json
from typing import Dict, Any


def bailian_400_arrearage_response() -> Dict[str, Any]:
    """Return a response simulating HTTP 400 with Arrearage code"""
    return {
        "status": 400,
        "body": {
            "error": {
                "code": "Arrearage",
                "message": "Account balance insufficient"
            }
        },
        "headers": {},
        "request_id": "test-arrearage-req-001"
    }


def bailian_403_freetier_response() -> Dict[str, Any]:
    """Return a response simulating HTTP 403 with FreeTierOnly allocation quota"""
    return {
        "status": 403,
        "body": {
            "error": {
                "code": "AllocationQuota.FreeTierOnly",
                "message": "This API is only available for free tier users"
            }
        },
        "headers": {},
        "request_id": "test-freetier-req-001"
    }


def rfc6585_429_with_retry_after_response() -> Dict[str, Any]:
    """Return a response simulating HTTP 429 with Retry-After header"""
    return {
        "status": 429,
        "body": {
            "error": {
                "message": "Rate limit exceeded"
            }
        },
        "headers": {
            "Retry-After": "60"  # 60 seconds
        },
        "request_id": "test-rate-limit-req-001"
    }


def drop_mid_response() -> Dict[str, Any]:
    """Simulate a connection drop or timeout mid-response"""
    return {
        "status": None,  # Indicates connection failure
        "body": "",
        "headers": {},
        "error_kind": "ReadTimeout",  # Or ConnectionError
        "request_id": "test-timeout-req-001"
    }


def budget_insufficient_scenario() -> Dict[str, Any]:
    """Define a scenario where budget is insufficient"""
    return {
        "budget_limit": 0.01,  # Very small budget in USD
        "current_spent": 0.009,
        "next_request_cost": 0.01,  # Would exceed budget
        "scenario_description": "Attempting to make a request that would exceed the budget limit"
    }


def all_candidates_down_scenario() -> Dict[str, Any]:
    """Define a scenario where all candidates/providers are unavailable"""
    return {
        "providers": ["evomap", "dashscope", "bailian"],
        "num_consecutive_failures": 10,
        "failure_reason": "All providers returning errors or timing out",
        "fallback_strategy": "Stop and report all providers unavailable",
        "max_retries_per_provider": 3,
        "circuit_breaker_threshold": 5
    }