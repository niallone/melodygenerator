"""
Tests for the authentication endpoints (login and logout).
"""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_login_missing_fields(app_with_mock_db, mock_db):
    """POST /auth/login with empty body returns a validation or bad request error."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/login", json={})

    # Pydantic validation will reject missing required fields (email, password)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials(app_with_mock_db, mock_db):
    """POST /auth/login with non-existent email returns 401."""
    mock_db.fetchrow = AsyncMock(return_value=None)

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )

    assert response.status_code == 401
    data = response.json()
    assert "message" in data
    assert "invalid" in data["message"].lower() or "email" in data["message"].lower()


@pytest.mark.asyncio
async def test_logout_returns_success(app_with_mock_db):
    """POST /auth/logout returns a success message."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "logged out" in data["message"].lower() or "success" in data["message"].lower()
