"""Database-related error classes."""

from .api import APIError


class DatabaseError(APIError):
    """Error raised when a database operation fails (500)."""

    def __init__(self, message="Database error occurred", payload=None):
        super().__init__(message, status_code=500, payload=payload)
