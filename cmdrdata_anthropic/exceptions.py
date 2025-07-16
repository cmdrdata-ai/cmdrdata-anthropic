"""
Custom exceptions for cmdrdata-openai package
"""

from typing import Any, Dict, Optional


class CmdrDataError(Exception):
    """Base exception for all cmdrdata-openai errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        base_message = self.message
        if self.error_code:
            base_message = f"[{self.error_code}] {base_message}"
        return base_message


# Alias for backward compatibility and consistent naming
CMDRDataError = CmdrDataError


class ConfigurationError(CmdrDataError):
    """Raised when there's a configuration issue"""

    pass


class AuthenticationError(CmdrDataError):
    """Raised when authentication fails"""

    pass


class ValidationError(CmdrDataError):
    """Raised when input validation fails"""

    pass


class RateLimitError(CmdrDataError):
    """Raised when rate limits are exceeded"""

    pass


class TrackingError(CmdrDataError):
    """Raised when usage tracking fails"""

    pass


class NetworkError(CmdrDataError):
    """Raised when network operations fail"""

    pass


class TimeoutError(CmdrDataError):
    """Raised when operations time out"""

    pass


class RetryExhaustedError(CmdrDataError):
    """Raised when retry attempts are exhausted"""

    pass


class CircuitBreakerError(CmdrDataError):
    """Raised when circuit breaker is open"""

    pass


class SecurityError(CmdrDataError):
    """Raised when security validation fails"""

    pass


class CompatibilityError(CmdrDataError):
    """Raised when version compatibility check fails"""

    pass
