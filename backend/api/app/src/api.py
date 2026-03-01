import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.database.postgres.database import pg_db
from app.src.config import Settings
from app.src.errors.handlers import register_error_handlers
from app.src.routes import router as routes_router
from app.src.services.melody_generator import get_available_models
from app.src.utils.logging import LoggingMiddleware

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the FastAPI app."""
    # Startup
    app.state.pg_db = await pg_db.get_instance()

    logger.info("Preloading melody generation models")
    try:
        settings = Settings()
        models = await get_available_models(settings.model_dir)
        app.state.models = models
        logger.info(f"Loaded models: {list(models.keys())}")
    except Exception as e:
        logger.error(f"Error preloading models: {str(e)}")
        app.state.models = {}

    yield

    # Shutdown
    if hasattr(app.state, "pg_db"):
        await app.state.pg_db.close()
        logger.info("Database connection closed")


def create_api() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application
    """
    settings = Settings()

    api = FastAPI(
        title="Melody Generator API",
        lifespan=lifespan,
    )

    # Store settings and limiter in app state
    api.state.settings = settings
    api.state.limiter = limiter
    api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Configure CORS
    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
    )

    # Security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response: Response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            return response

    api.add_middleware(SecurityHeadersMiddleware)

    # Configure logging middleware
    api.add_middleware(LoggingMiddleware)

    # Configure logging
    logging.basicConfig(level=getattr(logging, settings.logging_level, logging.INFO))

    # Register error handlers
    register_error_handlers(api)

    # Register routes
    api.include_router(routes_router)

    return api
