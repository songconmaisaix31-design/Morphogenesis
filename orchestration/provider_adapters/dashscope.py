"""DashScope provider adapter for failure classification."""

import json
from typing import Any, Dict
from pydantic import BaseModel

from .base import FailureClassification, ProviderAdapter, RequestContext


class DashScopeAdapter(ProviderAdapter):
    """Provider adapter for DashScope API responses."""
    
    @staticmethod
    def interpret(response_body: str, status_code: int, headers: Dict[str, str], 
                  request_context: RequestContext) -> FailureClassification:
        """
        Interpret DashScope API response and classify the failure.
        
        Args:
            response_body: Raw response body as string
            status_code: HTTP status code
            headers: Response headers dictionary
            request_context: Context about the request
            
        Returns:
            FailureClassification indicating the type of failure
        """
        # Handle various status codes
        if status_code == 429:
            return FailureClassification.CONFIRMED_REJECTION
        
        if status_code >= 400:
            try:
                # Parse response body as JSON if possible
                body_data: Dict[str, Any] = json.loads(response_body)
                
                # Check for specific error conditions
                if "Code" in body_data or "code" in body_data:
                    error_code = body_data.get("Code", body_data.get("code", ""))
                    error_message = body_data.get("Message", body_data.get("message", "")).lower()
                    
                    # Arrearage or billing issues
                    if "Arrearage" in str(error_code) or "arrearage" in str(error_code):
                        return FailureClassification.CONFIRMED_REJECTION
                    
                    # Free tier allocation issues
                    if "AllocationQuota.FreeTierOnly" in str(error_code):
                        return FailureClassification.CONFIRMED_REJECTION
                    
                    # Budget exhausted cases
                    budget_keywords = ["insufficient balance", "account balance", "payment required", "billing"]
                    if any(keyword in error_message for keyword in budget_keywords):
                        return FailureClassification.BUDGET_EXHAUSTED
                    
                    # Capability mismatch
                    capability_keywords = ["model not found", "unsupported", "not available", "invalid parameter"]
                    if any(keyword in error_message for keyword in capability_keywords):
                        return FailureClassification.CAPABILITY_MISMATCH
                
                # Generic client errors (4xx) are usually rejections
                if 400 <= status_code < 500:
                    return FailureClassification.CONFIRMED_REJECTION
                    
            except json.JSONDecodeError:
                # If response isn't JSON, try to classify based on status code
                if 400 <= status_code < 500:
                    return FailureClassification.CONFIRMED_REJECTION
        
        # Server errors (5xx) or connection issues are usually unknown effect
        if status_code >= 500:
            return FailureClassification.UNKNOWN_EFFECT
            
        # If we couldn't determine the classification, default to unknown
        return FailureClassification.UNKNOWN_EFFECT