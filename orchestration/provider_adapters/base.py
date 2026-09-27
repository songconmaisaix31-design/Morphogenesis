"""Base interface for provider-specific failure classification."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from enum import Enum
import math
import re
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
    classification: Optional[FailureClassification] = None
    normalized_reason: Optional[str] = None
    retry_after_raw: Optional[str] = None
    retry_after_seconds: Optional[float] = None


class ProviderAdapter:
    """Interface for provider-specific response interpretation."""
    
    @staticmethod
    def parse_retry_after(retry_after_header: str, now_utc: Optional[datetime] = None) -> Optional[float]:
        """
        Parse Retry-After header according to RFC standards using proper timezone-aware parsing.

        Args:
            retry_after_header: Value of Retry-After header
            now_utc: Optional datetime to use as current time for date calculations (for testing)

        Returns:
            Number of seconds to wait as float, or None if malformed
        """
        if retry_after_header is None:
            return None
            
        # Check if it's a valid integer string (only ASCII digits, possibly with leading +/- sign)
        # Reject floats, scientific notation, underscores, and non-ASCII digits
        stripped = retry_after_header.strip()
        
        # Check if it contains only ASCII digits (and possibly a single +/- sign at the start)
        # This rejects floats (containing '.'), scientific notation (containing 'e'/'E'),
        # underscores, and non-ASCII digits
        if re.fullmatch(r'[+-]?\d+', stripped) and all(ord(c) < 128 for c in stripped):
            try:
                value = int(stripped)
                # According to RFC, negative values are invalid
                if value < 0:
                    return None
                # Check for potential overflow (using a reasonable upper limit)
                # Python integers can be arbitrarily large, so we need to check before converting to float
                if abs(value) > 10**15:  # Very high limit to avoid practical overflow issues
                    return None
                return float(value)
            except (ValueError, OverflowError):
                return None
        else:
            # Try to parse as HTTP-date using email.utils.parsedate_to_datetime for timezone awareness
            try:
                dt = parsedate_to_datetime(retry_after_header)
                if dt is None:
                    return None
                # Use provided time or current UTC time
                current_time = now_utc or datetime.now(timezone.utc)
                if dt.tzinfo is None:
                    # Assume UTC if no timezone info
                    dt = dt.replace(tzinfo=timezone.utc)
                
                delta = (dt - current_time).total_seconds()
                # Return non-negative value
                return max(0.0, float(delta)) if not math.isnan(delta) and not math.isinf(delta) else None
            except (ValueError, TypeError, AttributeError):
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