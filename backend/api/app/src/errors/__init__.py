"""Custom error classes and error handling utilities for the API."""

from .api import APIError
from .database import DatabaseError
from .handlers import register_error_handlers
from .http import BadRequestError, NotFoundError
from .validation import ValidationError

__all__ = [
    "APIError",
    "NotFoundError",
    "BadRequestError",
    "DatabaseError",
    "ValidationError",
    "register_error_handlers",
]
