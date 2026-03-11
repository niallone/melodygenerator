"""Validation-related error classes."""

from .api import APIError


class ValidationError(APIError):
    """Error raised when data validation fails."""

    def __init__(self, message="Validation error", payload=None):
        super().__init__(message, status_code=422, payload=payload)
