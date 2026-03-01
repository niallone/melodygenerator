"""
This module contains functions for registering error handlers with the FastAPI application.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api import APIError
from .auth import AuthenticationError, AuthorisationError
from .database import DatabaseError
from .http import BadRequestError, MethodNotAllowedError, NotFoundError
from .validation import ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI):
    """
    Register error handlers for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

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

    @app.exception_handler(AuthenticationError)
    async def handle_authentication_error(request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content=exc.to_dict())

    @app.exception_handler(AuthorisationError)
    async def handle_authorisation_error(request: Request, exc: AuthorisationError):
        return JSONResponse(status_code=403, content=exc.to_dict())

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
