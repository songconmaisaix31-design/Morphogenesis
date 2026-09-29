"""HTTP 429 Rate Limit with Retry-After fault injection fixture"""

from typing import Dict, Any
import httpx


def create_rfc6585_429_with_retry_after_handler(request: httpx.Request) -> httpx.Response:
    """Create a handler that returns a 429 Rate Limit response with Retry-After header"""
    return httpx.Response(
        429,
        json={
            "error": {
                "message": "Rate limit exceeded, please try again later"
            }
        },
        headers={
            "x-request-id": "test-rate-limit-req-001",
            "Retry-After": "60"  # 60 seconds
        }
    )


# Direct response data for use in other tests
RFC6585_429_WITH_RETRY_AFTER_DATA = {
    "status_code": 429,
    "json_data": {
        "error": {
            "message": "Rate limit exceeded, please try again later"
        }
    },
    "headers": {
        "x-request-id": "test-rate-limit-req-001",
        "Retry-After": "60"
    }
}