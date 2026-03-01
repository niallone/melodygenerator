"""
Tests for the melody models endpoint (GET /melody/models).
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_get_models_empty(app_with_mock_db):
    """GET /melody/models returns an empty list when no models are loaded."""
    app_with_mock_db.state.models = {}

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/models")

    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_models_list(app_with_mock_db, mock_models):
    """GET /melody/models returns a list of model dicts with expected fields."""
    app_with_mock_db.state.models = mock_models

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/models")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    model = data[0]
    assert "id" in model
    assert "name" in model
    assert "architecture" in model
    assert "version" in model

    assert model["id"] == "test_model"
    assert model["name"] == "test_model"
    assert model["architecture"] == "lstm"
    assert model["version"] == 2
