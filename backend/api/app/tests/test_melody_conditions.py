"""Tests for the melody instruments endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient


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

    for instrument in data:
        assert "id" in instrument
        assert "name" in instrument
        assert isinstance(instrument["id"], int)
        assert isinstance(instrument["name"], str)

    piano = next((inst for inst in data if inst["id"] == 0), None)
    assert piano is not None
    assert piano["name"] == "Acoustic Grand Piano"
