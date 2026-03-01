"""
Tests for the main API routes (health check and index).
"""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health_check(app_with_mock_db, mock_db):
    """GET /health returns 200 with healthy status when DB is up."""
    mock_db.fetchval = AsyncMock(return_value=1)

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_db_down(app_with_mock_db, mock_db):
    """GET /health returns unhealthy status when the database is unreachable."""
    mock_db.fetchval = AsyncMock(side_effect=Exception("Connection refused"))

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "error"
    assert "message" in data


@pytest.mark.asyncio
async def test_index(app_with_mock_db):
    """GET / returns the welcome message."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "Welcome" in response.json() or "Melodygenerator" in response.json()
