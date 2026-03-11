from fastapi import Request

from app.src.config import Settings

_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_db(request: Request):
    """Get database instance from app state."""
    return request.app.state.pg_db


def get_models(request: Request):
    """Get loaded models from app state."""
    return request.app.state.models
