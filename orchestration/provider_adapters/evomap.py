"""EvoMap provider adapter for failure classification."""

import json
import re
from typing import Any, Dict
from pydantic import BaseModel

from .base import FailureClassification, ProviderAdapter, RequestContext, ClassificationResult


class EvoMapAdapter(ProviderAdapter):
    """Provider adapter for EvoMap API responses."""
    
    @staticmethod
    def interpret(response_body: str, status_code: int, headers: Dict[str, str], 
                  request_context: RequestContext) -> ClassificationResult:
        """
        Interpret EvoMap API response and classify the failure.
        
        Args:
            response_body: Raw response body as string
            status_code: HTTP status code
            headers: Response headers dictionary
            request_context: Context about the request
            
        Returns:
            ClassificationResult with classification and normalized reason
        """
        # Extract Retry-After header if present
        retry_after_raw = headers.get("Retry-After")
        retry_after_seconds = ProviderAdapter.parse_retry_after(retry_after_raw) if retry_after_raw else None
        
        # Handle transport errors - these take precedence over status/body
        if status_code == 0:  # Represents connection issues
            return ClassificationResult(
                classification=FailureClassification.UNKNOWN_EFFECT,
                normalized_reason="connection_failure",
                retry_after_raw=retry_after_raw,
                retry_after_seconds=retry_after_seconds
            )
        
        # Handle various status codes
        if status_code == 429:
            return ClassificationResult(
                classification=FailureClassification.CONFIRMED_REJECTION,
                normalized_reason="rate_limited",
                retry_after_raw=retry_after_raw,
                retry_after_seconds=retry_after_seconds
            )
        
        if status_code >= 400:
            try:
                # Parse response body as JSON if possible
                body_data: Dict[str, Any] = json.loads(response_body)
                
                # Check for specific error conditions
                if "error" in body_data:
                    error_info = body_data["error"]
                    
                    if isinstance(error_info, dict):
                        error_code = error_info.get("code", "")
                        # Safely handle null values for message
                        error_message_raw = error_info.get("message")
                        error_message = error_message_raw.lower() if error_message_raw and isinstance(error_message_raw, str) else ""
                        
                        # Arrearage indicates billing issue
                        if "arrearage" in str(error_code).lower():
                            return ClassificationResult(
                                classification=FailureClassification.CONFIRMED_REJECTION,
                                normalized_reason="billing_arrearage",
                                retry_after_raw=retry_after_raw,
                                retry_after_seconds=retry_after_seconds
                            )
                        
                        # Allocation quota free tier only
                        if "allocationquota.freetieronly" in str(error_code).lower():
                            return ClassificationResult(
                                classification=FailureClassification.CONFIRMED_REJECTION,
                                normalized_reason="free_tier_quota_exceeded",
                                retry_after_raw=retry_after_raw,
                                retry_after_seconds=retry_after_seconds
                            )
                            
                        # Check for budget-related messages
                        budget_keywords = ["insufficient funds", "payment required", "billing", "quota exceeded"]
                        if any(keyword in error_message for keyword in budget_keywords):
                            return ClassificationResult(
                                classification=FailureClassification.BUDGET_EXHAUSTED,
                                normalized_reason="insufficient_funds",
                                retry_after_raw=retry_after_raw,
                                retry_after_seconds=retry_after_seconds
                            )
                            
                        # Capability mismatch
                        capability_keywords = ["model not found", "unsupported", "not available"]
                        if any(keyword in error_message for keyword in capability_keywords):
                            return ClassificationResult(
                                classification=FailureClassification.CAPABILITY_MISMATCH,
                                normalized_reason="capability_unavailable",
                                retry_after_raw=retry_after_raw,
                                retry_after_seconds=retry_after_seconds
                            )
                
                # Generic client errors (4xx) are usually rejections
                if 400 <= status_code < 500:
                    return ClassificationResult(
                        classification=FailureClassification.CONFIRMED_REJECTION,
                        normalized_reason=f"http_{status_code}",
                        retry_after_raw=retry_after_raw,
                        retry_after_seconds=retry_after_seconds
                    )
                    
            except json.JSONDecodeError:
                # If response isn't JSON, try to classify based on status code
                if 400 <= status_code < 500:
                    return ClassificationResult(
                        classification=FailureClassification.CONFIRMED_REJECTION,
                        normalized_reason=f"http_{status_code}_non_json",
                        retry_after_raw=retry_after_raw,
                        retry_after_seconds=retry_after_seconds
                    )
        
        # Server errors (5xx) or connection issues are usually unknown effect
        if status_code >= 500:
            return ClassificationResult(
                classification=FailureClassification.UNKNOWN_EFFECT,
                normalized_reason=f"http_{status_code}",
                retry_after_raw=retry_after_raw,
                retry_after_seconds=retry_after_seconds
            )
            
        # If we couldn't determine the classification, default to unknown
        return ClassificationResult(
            classification=FailureClassification.UNKNOWN_EFFECT,
            normalized_reason="unknown_classification",
            retry_after_raw=retry_after_raw,
            retry_after_seconds=retry_after_seconds
        )