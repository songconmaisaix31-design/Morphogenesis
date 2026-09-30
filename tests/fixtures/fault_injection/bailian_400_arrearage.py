"""HTTP 400 Arrearage fault injection fixture"""

from typing import Dict, Any
import httpx


def create_bailian_400_arrearage_handler(request: httpx.Request) -> httpx.Response:
    """Create a handler that returns a 400 Arrearage response for fault injection"""
    return httpx.Response(
        400,
        json={
            "error": {
                "code": "Arrearage",
                "message": "Account balance insufficient for the requested operation"
            }
        },
        headers={"x-request-id": "test-arrearage-req-001"}
    )


# Direct response data for use in other tests
BAILIAN_400_ARREARAGE_DATA = {
    "status_code": 400,
    "json_data": {
        "error": {
            "code": "Arrearage",
            "message": "Account balance insufficient for the requested operation"
        }
    },
    "headers": {"x-request-id": "test-arrearage-req-001"}
}