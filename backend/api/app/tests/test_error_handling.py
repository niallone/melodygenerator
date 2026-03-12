"""
Tests for error handling behavior across the API.

Verifies that errors are returned in a consistent format, that 500 responses
do not leak tracebacks, and that security headers are present on responses.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_unexpected_error_no_traceback(app_with_mock_db):
    """500 error responses must not include a 'traceback' field in the JSON body."""

    @app_with_mock_db.get("/test-unexpected-500")
    async def trigger_500():
        raise RuntimeError("Something broke internally")

    transport = ASGITransport(app=app_with_mock_db, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-unexpected-500")

    assert response.status_code == 500
    body = response.text
    assert "Traceback" not in body
    assert "trigger_500" not in body


@pytest.mark.asyncio
async def test_not_found_error(app_with_mock_db):
    """404 errors return a JSON body with a 'message' field."""
    from app.src.errors import NotFoundError

    @app_with_mock_db.get("/test-not-found-handler")
    async def trigger_404():
        raise NotFoundError("Resource does not exist")

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test-not-found-handler")

    assert response.status_code == 404
    data = response.json()
    assert "message" in data
    assert data["message"] == "Resource does not exist"


@pytest.mark.asyncio
async def test_security_headers_present(app_with_mock_db):
    """Responses include security headers: X-Content-Type-Options, X-Frame-Options, etc."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200

    # Check security headers added by SecurityHeadersMiddleware
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert "strict-transport-security" in response.headers
    assert "referrer-policy" in response.headers
