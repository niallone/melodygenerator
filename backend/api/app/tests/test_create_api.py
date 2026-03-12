"""Tests for the create_api factory function."""

from fastapi import FastAPI

from app.src.api import create_api


class TestCreateApi:
    def test_returns_fastapi_instance(self):
        app = create_api()
        assert isinstance(app, FastAPI)

    def test_settings_in_state(self):
        app = create_api()
        assert hasattr(app.state, "settings")

    def test_limiter_in_state(self):
        app = create_api()
        assert hasattr(app.state, "limiter")

    def test_routes_registered(self):
        app = create_api()
        paths = [route.path for route in app.routes]
        assert "/health" in paths
        assert "/" in paths
