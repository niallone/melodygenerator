"""
This module defines authentication and authorisation related error classes.

These classes extend the base APIError class to provide specific error types
for authentication and authorisation failures.
"""

from .api import APIError


class AuthenticationError(APIError):
    """
    Error raised when authentication fails.

    This could be due to invalid credentials, expired tokens, etc.
    """

    def __init__(self, message="Authentication failed", payload=None):
        """
        Initialise an AuthenticationError.

        Args:
            message (str): A description of the authentication error. Defaults to "Authentication failed".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=401, payload=payload)


class AuthorisationError(APIError):
    """
    Error raised when a user is not authorised to perform an action.

    This is typically used when a user is authenticated but lacks the necessary permissions.
    """

    def __init__(self, message="Not authorised", payload=None):
        """
        Initialise an AuthorisationError.

        Args:
            message (str): A description of the authorisation error. Defaults to "Not authorised".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=403, payload=payload)


# Add more authentication/authorisation-related errors as needed
