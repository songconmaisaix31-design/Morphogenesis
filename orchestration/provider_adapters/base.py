"""Base interface for provider-specific failure classification."""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel


class FailureClassification(str, Enum):
    CONFIRMED_REJECTION = "confirmed_rejection"
    UNKNOWN_EFFECT = "unknown_effect"
    BUDGET_EXHAUSTED = "budget_exhausted"
    CAPABILITY_MISMATCH = "capability_mismatch"


class RequestContext(BaseModel):
    """Context about the request that may influence classification."""
    provider: str
    model: str
    endpoint: str


class ProviderAdapter:
    """Interface for provider-specific response interpretation."""
    
    @staticmethod
    def interpret(response_body: str, status_code: int, headers: Dict[str, str], 
                  request_context: RequestContext) -> FailureClassification:
        """
        Interpret a response and classify the failure type.
        
        Args:
            response_body: Raw response body as string
            status_code: HTTP status code
            headers: Response headers dictionary
            request_context: Context about the request
            
        Returns:
            FailureClassification indicating the type of failure
        """
        raise NotImplementedError