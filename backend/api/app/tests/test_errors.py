"""
This module contains unit tests for the custom error classes defined in the app.src.errors module.
These tests ensure that each error type is correctly instantiated with the expected attributes.
"""

from app.src.errors import (
    APIError,
    AuthenticationError,
    AuthorisationError,
    BadRequestError,
    DatabaseError,
    NotFoundError,
)


def test_api_error():
    """
    Test the base APIError class.

    This test checks if the APIError is correctly instantiated with custom message,
    status code, and payload. It also verifies the to_dict() method.
    """
    error = APIError("Test error", status_code=418, payload={"detail": "I'm a teapot"})
    assert error.message == "Test error"
    assert error.status_code == 418
    assert error.to_dict() == {"message": "Test error", "detail": "I'm a teapot"}


def test_not_found_error():
    """
    Test the NotFoundError class.

    This test verifies that NotFoundError is correctly instantiated with a custom message
    and has the expected status code of 404.
    """
    error = NotFoundError("User not found")
    assert error.message == "User not found"
    assert error.status_code == 404


def test_bad_request_error():
    """
    Test the BadRequestError class.

    This test checks if BadRequestError is correctly instantiated with the default message
    and has the expected status code of 400.
    """
    error = BadRequestError()
    assert error.message == "Bad request"
    assert error.status_code == 400


def test_database_error():
    """
    Test the DatabaseError class.

    This test verifies that DatabaseError is correctly instantiated with a custom message
    and has the expected status code of 500.
    """
    error = DatabaseError("Connection failed")
    assert error.message == "Connection failed"
    assert error.status_code == 500


def test_authentication_error():
    """
    Test the AuthenticationError class.

    This test checks if AuthenticationError is correctly instantiated with the default message
    and has the expected status code of 401.
    """
    error = AuthenticationError()
    assert error.message == "Authentication failed"
    assert error.status_code == 401


def test_authorisation_error():
    """
    Test the AuthorisationError class.

    This test verifies that AuthorisationError is correctly instantiated with a custom message
    and has the expected status code of 403.
    """
    error = AuthorisationError("Insufficient permissions")
    assert error.message == "Insufficient permissions"
    assert error.status_code == 403
