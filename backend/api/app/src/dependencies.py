from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.src.config import Settings

_settings = None

limiter = Limiter(key_func=get_remote_address)


def get_limiter() -> Limiter:
    return limiter


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
