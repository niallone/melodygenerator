"""HTTP-specific error classes."""

from .api import APIError


class NotFoundError(APIError):
    """Error raised when a requested resource is not found (404)."""

    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)


class BadRequestError(APIError):
    """Error raised when the client sends an invalid request (400)."""

    def __init__(self, message="Bad request", payload=None):
        super().__init__(message, status_code=400, payload=payload)
