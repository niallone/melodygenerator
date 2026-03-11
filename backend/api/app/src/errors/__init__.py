"""
Custom error classes and error handling utilities for the API.
"""

from .api import APIError
from .database import DatabaseError
from .handlers import register_error_handlers
from .http import BadRequestError, MethodNotAllowedError, NotFoundError
from .validation import ValidationError

__all__ = [
    "APIError",
    "NotFoundError",
    "BadRequestError",
    "MethodNotAllowedError",
    "DatabaseError",
    "ValidationError",
    "register_error_handlers",
]
