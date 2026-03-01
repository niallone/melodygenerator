"""
This package contains custom error classes and error handling utilities for the API.

Modules:
- api: Defines the base APIError class.
- http: Contains HTTP-specific error classes.
- database: Defines database-related error classes.
- auth: Provides authentication and authorisation error classes.
- handlers: Contains functions for registering error handlers with the FastAPI app.
"""

from .api import APIError
from .auth import AuthenticationError, AuthorisationError
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
    "AuthenticationError",
    "AuthorisationError",
    "ValidationError",
    "register_error_handlers",
]
