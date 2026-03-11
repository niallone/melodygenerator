"""
Tests for the melody download endpoint, focusing on path traversal prevention.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_download_path_traversal_blocked(app_with_mock_db):
    """GET /melody/download/../../etc/passwd returns 400 to prevent path traversal."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/download/../../etc/passwd")

    # The route should either return 400 (explicit rejection) or 404/422 (path not matched)
    # Path traversal attempts must not return file contents
    assert response.status_code in (400, 404, 422)


@pytest.mark.asyncio
async def test_download_file_not_found(app_with_mock_db):
    """GET /melody/download/nonexistent.mid returns an error for missing files."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/melody/download/nonexistent.mid")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_dotdot_blocked(app_with_mock_db):
    """GET /melody/download/ with URL-encoded path traversal is blocked."""
    transport = ASGITransport(app=app_with_mock_db)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Use a filename that contains '..' after URL decoding
        response = await client.get("/melody/download/..%2F..%2Fetc%2Fpasswd")

    # Should be rejected - either 400 from validation, 404 from routing, or 422
    assert response.status_code in (400, 404, 422)
