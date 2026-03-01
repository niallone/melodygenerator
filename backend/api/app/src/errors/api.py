"""
This module defines the base APIError class for custom API exceptions.
"""


class APIError(Exception):
    """
    A custom exception class for API-related errors.

    This class extends the built-in Exception class and adds attributes
    for status code and payload. It's designed to be used for all
    API-specific exceptions, allowing for consistent error handling
    and reporting across the application.

    Attributes:
        message (str): A human-readable description of the error.
        status_code (int): The HTTP status code associated with this error.
        payload (dict, optional): Additional data to be included in the error response.

    Methods:
        to_dict(): Converts the error information to a dictionary for JSON serialisation.
    """

    def __init__(self, message, status_code=400, payload=None):
        """
        Initialise a new APIError instance.

        Args:
            message (str): A description of the error.
            status_code (int, optional): The HTTP status code. Defaults to 400.
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """
        Convert the APIError instance to a dictionary.

        This method is useful for serialising the error information
        to JSON for API responses.

        Returns:
            dict: A dictionary representation of the error.
        """
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

    def __str__(self):
        return self.message if self.message else "An API error occurred"
