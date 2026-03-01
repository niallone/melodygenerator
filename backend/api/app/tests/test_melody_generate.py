"""
Tests for the melody generation endpoint (POST /melody/generate).
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_generate_missing_model(app_with_mock_db, mock_db):
    """POST /melody/generate with empty model_id returns 400."""
    app_with_mock_db.state.models = {}

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/melody/generate",
            json={
                "model_id": "",
            },
        )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "model_id" in data["detail"].lower() or "model" in data["detail"].lower()


@pytest.mark.asyncio
async def test_generate_invalid_params(app_with_mock_db, mock_db):
    """POST /melody/generate with temperature > 2.0 returns 422 validation error."""
    app_with_mock_db.state.models = {}

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/melody/generate",
            json={
                "model_id": "test_model",
                "temperature": 5.0,
            },
        )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
