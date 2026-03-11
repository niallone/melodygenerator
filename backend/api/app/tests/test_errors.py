"""Unit tests for the custom error classes."""

from app.src.errors import (
    APIError,
    BadRequestError,
    DatabaseError,
    NotFoundError,
)


def test_api_error():
    error = APIError("Test error", status_code=418, payload={"detail": "I'm a teapot"})
    assert error.message == "Test error"
    assert error.status_code == 418
    assert error.to_dict() == {"message": "Test error", "detail": "I'm a teapot"}


def test_not_found_error():
    error = NotFoundError("User not found")
    assert error.message == "User not found"
    assert error.status_code == 404


def test_bad_request_error():
    error = BadRequestError()
    assert error.message == "Bad request"
    assert error.status_code == 400


def test_database_error():
    error = DatabaseError("Connection failed")
    assert error.message == "Connection failed"
    assert error.status_code == 500
