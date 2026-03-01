"""
Top-level conftest file for pytest configuration.
"""

import pytest

pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio coroutine")


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def asyncio_default_fixture_loop_scope():
    return "session"
