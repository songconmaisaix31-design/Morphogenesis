"""HTTP 403 Free Tier Only fault injection fixture"""

from typing import Dict, Any
import httpx


def create_bailian_403_freetier_handler(request: httpx.Request) -> httpx.Response:
    """Create a handler that returns a 403 Free Tier Only response for fault injection"""
    return httpx.Response(
        403,
        json={
            "error": {
                "code": "AllocationQuota.FreeTierOnly",
                "message": "This API is only available for free tier users"
            }
        },
        headers={"x-request-id": "test-freetier-req-001"}
    )


# Direct response data for use in other tests
BAILIAN_403_FREETIER_DATA = {
    "status_code": 403,
    "json_data": {
        "error": {
            "code": "AllocationQuota.FreeTierOnly",
            "message": "This API is only available for free tier users"
        }
    },
    "headers": {"x-request-id": "test-freetier-req-001"}
}