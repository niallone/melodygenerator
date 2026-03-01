"""
Tests for the melody conditions and instruments endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_get_conditions(app_with_mock_db):
    """GET /melody/conditions returns a dict with keys, tempos, and styles."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/conditions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "keys" in data
    assert "tempos" in data
    assert "styles" in data

    assert isinstance(data["keys"], list)
    assert len(data["keys"]) > 0
    assert "Cmaj" in data["keys"]

    assert isinstance(data["tempos"], list)
    assert len(data["tempos"]) > 0
    assert 120 in data["tempos"]

    assert isinstance(data["styles"], list)
    assert len(data["styles"]) > 0
    assert "classical" in data["styles"]


@pytest.mark.asyncio
async def test_get_instruments(app_with_mock_db):
    """GET /melody/instruments returns a list of instruments with id and name."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/instruments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check that each instrument has the expected fields
    for instrument in data:
        assert "id" in instrument
        assert "name" in instrument
        assert isinstance(instrument["id"], int)
        assert isinstance(instrument["name"], str)

    # Verify that Acoustic Grand Piano (id 0) is included
    piano = next((inst for inst in data if inst["id"] == 0), None)
    assert piano is not None
    assert piano["name"] == "Acoustic Grand Piano"
