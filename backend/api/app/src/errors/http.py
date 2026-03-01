"""
This module defines HTTP-related error classes.

These classes extend the base APIError class to provide specific error types
for common HTTP error scenarios.
"""

from .api import APIError


class NotFoundError(APIError):
    """
    Error raised when a requested resource is not found.

    This typically corresponds to a 404 HTTP status code.
    """

    def __init__(self, message="Resource not found", payload=None):
        """
        Initialise a NotFoundError.

        Args:
            message (str): A description of what resource was not found. Defaults to "Resource not found".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=404, payload=payload)


class BadRequestError(APIError):
    """
    Error raised when the client sends an invalid request.

    This typically corresponds to a 400 HTTP status code and can be due to
    invalid parameters, malformed request body, etc.
    """

    def __init__(self, message="Bad request", payload=None):
        """
        Initialise a BadRequestError.

        Args:
            message (str): A description of why the request is bad. Defaults to "Bad request".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=400, payload=payload)


class MethodNotAllowedError(APIError):
    """
    Error raised when the HTTP method is not allowed for the requested resource.

    This typically corresponds to a 405 HTTP status code and occurs when
    a request method is not supported for the requested resource.
    """

    def __init__(self, message="Method not allowed", payload=None):
        """
        Initialise a MethodNotAllowedError.

        Args:
            message (str): A description of why the method is not allowed. Defaults to "Method not allowed".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=405, payload=payload)
