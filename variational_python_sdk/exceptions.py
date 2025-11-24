"""Custom exceptions for Variational SDK."""
from typing import Optional


class VariationalError(Exception):
    """Base exception for all Variational SDK errors."""
    pass


class VariationalAPIError(VariationalError):
    """Raised when the API returns an error response."""
    def __init__(self, status_code: int, message: str, response_body: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"API error {status_code}: {message}")


class VariationalAuthenticationError(VariationalAPIError):
    """Raised when authentication fails (401, 403)."""
    def __init__(self, status_code: int, message: str, response_body: Optional[str] = None):
        super().__init__(status_code, message, response_body)
        self.status_code = status_code


class VariationalRateLimitError(VariationalAPIError):
    """Raised when rate limit is exceeded (429)."""
    pass


class VariationalValidationError(VariationalError):
    """Raised when request validation fails."""
    pass

