"""
This module defines database-related error classes.

These classes extend the base APIError class to provide specific error types
for database operations and issues.
"""

from .api import APIError


class DatabaseError(APIError):
    """
    Error raised when a database operation fails.

    This could be due to connection issues, query errors, constraint violations, etc.
    """

    def __init__(self, message="Database error occurred", payload=None):
        """
        Initialise a DatabaseError.

        Args:
            message (str): A description of the database error. Defaults to "Database error occurred".
            payload (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message, status_code=500, payload=payload)


# Add more database-related errors as needed
# For example:
# class UniqueConstraintViolationError(DatabaseError):
#     def __init__(self, message="Unique constraint violated", payload=None):
#         super().__init__(message, status_code=409, payload=payload)
