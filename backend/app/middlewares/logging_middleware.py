import time
import uuid

from app.core.logging import logger
from app.core.security import decode_token
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Resolve Request ID and Correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id

        # Extract Client IP
        client_ip = request.client.host if request.client else "unknown"

        # Resolve User ID from Authorization Bearer token (if present)
        user_id = "anonymous"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                if payload:
                    user_id = payload.get("sub", "anonymous")
            except Exception:
                # Silently fall back to anonymous if token is malformed
                pass

        start_time = time.perf_counter()

        # Log request initiation details
        logger.info(
            f"Request Start - ID: {request_id} | Correlation: {correlation_id} | "
            f"User: {user_id} | IP: {client_ip} | "
            f"Method: {request.method} | Path: {request.url.path}"
        )

        try:
            response = await call_next(request)

            process_time_ms = (time.perf_counter() - start_time) * 1000

            # Attach header tracking identifiers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

            logger.info(
                f"Request End - ID: {request_id} | Correlation: {correlation_id} | "
                f"User: {user_id} | Status: {response.status_code} | "
                f"Time: {process_time_ms:.2f}ms"
            )
            return response

        except Exception as e:
            process_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request Exception - ID: {request_id} | Correlation: {correlation_id} | "
                f"User: {user_id} | Message: {e} | "
                f"Time: {process_time_ms:.2f}ms"
            )
            raise e
