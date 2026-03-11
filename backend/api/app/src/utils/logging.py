import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Attach request_id to request state for downstream use
        request.state.request_id = request_id

        path = request.url.path
        logger.info(
            json.dumps(
                {
                    "event": "request_start",
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                }
            )
        )

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            json.dumps(
                {
                    "event": "request_end",
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        )

        response.headers["X-Request-ID"] = request_id
        return response
