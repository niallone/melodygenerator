"""
This module defines validation-related error classes.

These classes extend the base APIError class to provide specific error types
for validation failures in the application.
"""

from .api import APIError


class ValidationError(APIError):
    """
    Error raised when data validation fails.

    This could be due to missing required fields, invalid data types,
    or any other validation rule violations.
    """

    def __init__(self, message="Validation error", payload=None):
        """
        Initialize a ValidationError.

        Args:
            message (str): A description of the validation error. Defaults to "Validation error".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=422, payload=payload)


class InvalidInputError(ValidationError):
    """
    Error raised when input data is invalid.

    This is a more specific type of ValidationError, used when the input
    data doesn't meet the expected format or constraints.
    """

    def __init__(self, message="Invalid input", payload=None):
        """
        Initialize an InvalidInputError.

        Args:
            message (str): A description of the invalid input. Defaults to "Invalid input".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, payload)


class MissingFieldError(ValidationError):
    """
    Error raised when a required field is missing from the input data.
    """

    def __init__(self, field_name, message=None, payload=None):
        """
        Initialize a MissingFieldError.

        Args:
            field_name (str): The name of the missing field.
            message (str, optional): A custom error message. If not provided, a default message is generated.
            payload (dict, optional): Additional error details. Defaults to None.
        """
        if message is None:
            message = f"Missing required field: {field_name}"
        super().__init__(message, payload)
        self.field_name = field_name
