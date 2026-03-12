"""Tests for the LoggingMiddleware."""

import json

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_request_id_in_response_header(app_with_mock_db):
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) == 8


@pytest.mark.asyncio
async def test_request_logs_start_and_end(app_with_mock_db, caplog):
    transport = ASGITransport(app=app_with_mock_db)
    with caplog.at_level("INFO"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/health")

    log_messages = [r.message for r in caplog.records]
    start_logs = [m for m in log_messages if "request_start" in m]
    end_logs = [m for m in log_messages if "request_end" in m]

    assert len(start_logs) >= 1
    assert len(end_logs) >= 1

    start_data = json.loads(start_logs[0])
    assert start_data["method"] == "GET"
    assert start_data["path"] == "/health"
    assert "request_id" in start_data
    assert "timestamp" in start_data

    end_data = json.loads(end_logs[0])
    assert end_data["status"] == 200
    assert "duration_ms" in end_data
    assert end_data["request_id"] == start_data["request_id"]
