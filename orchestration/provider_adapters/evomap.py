"""EvoMap provider adapter for failure classification."""

import json
from typing import Any, Dict
from pydantic import BaseModel

from .base import FailureClassification, ProviderAdapter, RequestContext


class EvoMapAdapter(ProviderAdapter):
    """Provider adapter for EvoMap API responses."""
    
    @staticmethod
    def interpret(response_body: str, status_code: int, headers: Dict[str, str], 
                  request_context: RequestContext) -> FailureClassification:
        """
        Interpret EvoMap API response and classify the failure.
        
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
                if "error" in body_data:
                    error_info = body_data["error"]
                    
                    if isinstance(error_info, dict):
                        error_code = error_info.get("code", "")
                        error_message = error_info.get("message", "").lower()
                        
                        # Arrearage indicates billing issue
                        if "arrearage" in str(error_code).lower():
                            return FailureClassification.CONFIRMED_REJECTION
                        
                        # Allocation quota free tier only
                        if "allocationquota.freetieronly" in str(error_code).lower():
                            return FailureClassification.CONFIRMED_REJECTION
                            
                        # Check for budget-related messages
                        budget_keywords = ["insufficient funds", "payment required", "billing", "quota exceeded"]
                        if any(keyword in error_message for keyword in budget_keywords):
                            return FailureClassification.BUDGET_EXHAUSTED
                            
                        # Capability mismatch
                        capability_keywords = ["model not found", "unsupported", "not available"]
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