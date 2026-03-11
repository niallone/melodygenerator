"""Tests for the gallery endpoint."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_gallery_returns_melodies(app_with_mock_db, mock_db):
    mock_db.fetch = AsyncMock(
        return_value=[
            {
                "id": 1,
                "model_id": "test",
                "instrument_name": "Piano",
                "midi_file": "test.mid",
                "wav_file": "test.wav",
                "temperature": 0.8,
                "num_notes": 500,
                "created": "2025-01-01T00:00:00",
                "total": 1,
            }
        ]
    )

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/gallery")

    assert response.status_code == 200
    data = response.json()
    assert "melodies" in data
    assert data["total"] == 1
    # total column should be stripped from individual melody objects
    assert "total" not in data["melodies"][0]


@pytest.mark.asyncio
async def test_gallery_empty(app_with_mock_db, mock_db):
    mock_db.fetch = AsyncMock(return_value=[])

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/gallery")

    assert response.status_code == 200
    data = response.json()
    assert data["melodies"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_gallery_respects_limit(app_with_mock_db, mock_db):
    mock_db.fetch = AsyncMock(return_value=[])

    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/gallery?limit=100")

    assert response.status_code == 200
    # Verify limit was capped to 50 in the query
    call_args = mock_db.fetch.call_args
    assert call_args[0][1] == 50  # min(100, 50)
