"""DashScope provider adapter for failure classification."""

import json
import re
from typing import Any, Dict
from pydantic import BaseModel

from .base import FailureClassification, ProviderAdapter, RequestContext, ClassificationResult


class DashScopeAdapter(ProviderAdapter):
    """Provider adapter for DashScope API responses."""
    
    @staticmethod
    def interpret(response_body: str, status_code: int, headers: Dict[str, str], 
                  request_context: RequestContext) -> ClassificationResult:
        """
        Interpret DashScope API response and classify the failure.
        
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
                if "Code" in body_data or "code" in body_data:
                    error_code = body_data.get("Code", body_data.get("code", ""))
                    # Safely handle null values for message
                    message_raw = body_data.get("Message", body_data.get("message"))
                    error_message = message_raw.lower() if message_raw and isinstance(message_raw, str) else ""
                    
                    # Arrearage or billing issues
                    if "Arrearage" in str(error_code) or "arrearage" in str(error_code):
                        return ClassificationResult(
                            classification=FailureClassification.CONFIRMED_REJECTION,
                            normalized_reason="billing_arrearage",
                            retry_after_raw=retry_after_raw,
                            retry_after_seconds=retry_after_seconds
                        )
                    
                    # Free tier allocation issues
                    if "AllocationQuota.FreeTierOnly" in str(error_code):
                        return ClassificationResult(
                            classification=FailureClassification.CONFIRMED_REJECTION,
                            normalized_reason="free_tier_quota_exceeded",
                            retry_after_raw=retry_after_raw,
                            retry_after_seconds=retry_after_seconds
                        )
                    
                    # Budget exhausted cases
                    budget_keywords = ["insufficient balance", "account balance", "payment required", "billing"]
                    if any(keyword in error_message for keyword in budget_keywords):
                        return ClassificationResult(
                            classification=FailureClassification.BUDGET_EXHAUSTED,
                            normalized_reason="insufficient_funds",
                            retry_after_raw=retry_after_raw,
                            retry_after_seconds=retry_after_seconds
                        )
                    
                    # Capability mismatch
                    capability_keywords = ["model not found", "unsupported", "not available", "invalid parameter"]
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
            
        # HTTP 200 with valid content should have no classification
        if status_code == 200:
            return ClassificationResult(
                classification=None,  # No classification for successful responses
                normalized_reason=None,
                retry_after_raw=retry_after_raw,
                retry_after_seconds=retry_after_seconds
            )

        # If we couldn't determine the classification for non-200 status, default to unknown
        return ClassificationResult(
            classification=FailureClassification.UNKNOWN_EFFECT,
            normalized_reason="unknown_classification",
            retry_after_raw=retry_after_raw,
            retry_after_seconds=retry_after_seconds
        )