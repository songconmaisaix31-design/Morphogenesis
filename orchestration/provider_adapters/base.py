"""Base interface for provider-specific failure classification."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from enum import Enum
import math
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


class ClassificationResult(BaseModel):
    """Result of classification containing both classification and normalized reason."""
    classification: FailureClassification
    normalized_reason: Optional[str] = None
    retry_after_raw: Optional[str] = None
    retry_after_seconds: Optional[float] = None


class ProviderAdapter:
    """Interface for provider-specific response interpretation."""
    
    @staticmethod
    def parse_retry_after(retry_after_header: str) -> Optional[float]:
        """
        Parse Retry-After header according to RFC standards using proper timezone-aware parsing.
        
        Args:
            retry_after_header: Value of Retry-After header
            
        Returns:
            Number of seconds to wait as float, or None if malformed
        """
        try:
            # Try to parse as seconds (integer only - reject floats/exponents)
            # Check if the string represents an integer (no decimal point or exponent)
            if '.' in retry_after_header or 'e' in retry_after_header.lower():
                return None  # Reject floats and scientific notation
            value = int(retry_after_header)
            # According to RFC, negative values are invalid
            if value < 0:
                return None
            return float(value)
        except ValueError:
            try:
                # Try to parse as HTTP-date using email.utils.parsedate_to_datetime for timezone awareness
                dt = parsedate_to_datetime(retry_after_header)
                if dt is None:
                    return None
                # Calculate difference from current time
                current_time = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
                delta = (dt - current_time).total_seconds()
                # Return non-negative value
                return max(0.0, float(delta)) if not math.isnan(delta) and not math.isinf(delta) else None
            except (ValueError, TypeError):
                # Malformed - return None
                return None
    
    @staticmethod
    def interpret(response_body: str, status_code: int, headers: Dict[str, str], 
                  request_context: RequestContext) -> ClassificationResult:
        """
        Interpret a response and classify the failure type.
        
        Args:
            response_body: Raw response body as string
            status_code: HTTP status code
            headers: Response headers dictionary
            request_context: Context about the request
            
        Returns:
            ClassificationResult with classification and normalized reason
        """
        raise NotImplementedError