"""Error handler registration for the FastAPI application."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api import APIError
from .database import DatabaseError
from .http import BadRequestError, MethodNotAllowedError, NotFoundError
from .validation import ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI):
    """Register error handlers for the FastAPI application."""

    @app.exception_handler(NotFoundError)
    async def handle_not_found_error(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content=exc.to_dict())

    @app.exception_handler(BadRequestError)
    async def handle_bad_request_error(request: Request, exc: BadRequestError):
        return JSONResponse(status_code=400, content=exc.to_dict())

    @app.exception_handler(MethodNotAllowedError)
    async def handle_method_not_allowed_error(request: Request, exc: MethodNotAllowedError):
        return JSONResponse(status_code=405, content=exc.to_dict())

    @app.exception_handler(DatabaseError)
    async def handle_database_error(request: Request, exc: DatabaseError):
        return JSONResponse(status_code=500, content=exc.to_dict())

    @app.exception_handler(ValidationError)
    async def handle_validation_error(request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content=exc.to_dict())

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("An unexpected error occurred.")
        error_details = {
            "error": "An unexpected error occurred.",
            "type": str(type(exc).__name__),
        }
        return JSONResponse(status_code=500, content=error_details)
