# error_handlers.py
"""
Error handling utilities for the Flask LLM Chat application.
This module provides custom exception classes and handler functions.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Custom exception classes
class LLMChatError(Exception):
    """Base exception class for all application-specific exceptions."""
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ModelInitializationError(LLMChatError):
    """Exception raised when LLM initialization fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)

class FileProcessingError(LLMChatError):
    """Exception raised when file processing fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)

class ConversationError(LLMChatError):
    """Exception raised when conversation handling fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)

class APIKeyError(LLMChatError):
    """Exception raised when API key is missing or invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=401, details=details)

class RateLimitError(LLMChatError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=429, details=details)

class ValidationError(LLMChatError):
    """Exception raised when input validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)

# Function to handle vendor-specific exceptions
def handle_vendor_exception(e: Exception, vendor: Enum) -> LLMChatError:
    """
    Maps vendor-specific exceptions to our custom exceptions.
    
    Args:
        e: The original exception
        vendor: The vendor name (e.g., 'openai', 'anthropic')
        
    Returns:
        An appropriate LLMChatError subclass
    """
    error_class = e.__class__.__name__
    error_msg = str(e)
    
    # Add details for logging
    details = {
        'original_exception': error_class,
        'vendor': vendor.VendorID.value
    }
    if 'RateLimitError' in error_class:
            return RateLimitError(vendor.RateLimitError.value, details)
    elif 'AuthenticationError' in error_class:
        return APIKeyError(vendor.AuthenticationError.value, details)
    elif 'APIError' in error_class:
        return ModelInitializationError(vendor.APIError.value.format(error_msg=error_msg), details)
    elif 'Timeout' in error_class:
        return ModelInitializationError(vendor.TimeoutError.value, details)
    
    # Default case
    return ModelInitializationError(f"{vendor.DisplayName.value} error: {error_msg}", details)

# Handler for all exceptions
def handle_exception(e: Exception) -> Tuple[Dict[str, Any], int]:
    """
    Handles exceptions and returns appropriate JSON response and status code.
    
    Args:
        e: The exception to handle
        
    Returns:
        Tuple of (response_json, status_code)
    """
    # Log the exception
    logger.error(f"Exception: {str(e)}")
    logger.error(traceback.format_exc())
    
    # Handle our custom exceptions
    if isinstance(e, LLMChatError):
        response = {
            'error': e.message,
            'code': e.code
        }
        
        # Include details if available and we're in debug mode
        if e.details and logger.level == logging.DEBUG:
            response['details'] = e.details
            
        return response, e.code
    
    # Handle unexpected exceptions
    return {
        'error': 'An unexpected error occurred. Please try again.',
        'code': 500
    }, 500