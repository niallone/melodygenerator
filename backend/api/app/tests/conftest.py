import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# Set test environment before importing app
os.environ["DEBUG"] = "true"

# Eagerly import create_api at module level so the heavy music21 dependency
# loads during collection (no per-test timeout) rather than during fixture setup.
from app.src.api import create_api  # noqa: E402


@asynccontextmanager
async def _noop_lifespan(app):
    yield


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def asyncio_default_fixture_loop_scope():
    return "session"


@pytest.fixture(scope="module")
def app() -> FastAPI:
    app = create_api()
    # Override lifespan so tests don't connect to real postgres or load models
    app.router.lifespan_context = _noop_lifespan
    app.state.settings.debug = True
    app.state.pg_db = None
    app.state.models = {}
    return app


@pytest.fixture
async def client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db():
    mock = AsyncMock()
    mock.fetchval = AsyncMock(return_value=1)
    mock.fetch = AsyncMock(return_value=[])
    mock.fetchrow = AsyncMock(return_value=None)
    mock.execute = AsyncMock(return_value="DELETE 1")
    return mock


@pytest.fixture
def app_with_mock_db(app: FastAPI, mock_db):
    app.state.pg_db = mock_db
    return app


@pytest.fixture
def mock_models():
    """Mock models dict with a fake model entry."""
    mock_model = MagicMock()
    mock_model.eval = MagicMock()
    mock_model.parameters = MagicMock(return_value=[])
    # Not a transformer (no d_model attribute)
    del mock_model.d_model

    return {
        "test_model": (
            mock_model,  # model
            [[0] * 100],  # seeds
            ["C4", "D4", "E4"],  # pitchnames
            {"C4": 0, "D4": 1, "E4": 2},  # note_to_int
            3,  # n_vocab
            2,  # model_version
            None,  # tokenizer
        )
    }
