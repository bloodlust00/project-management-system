import time

from app.core.config import settings
from app.core.logging import logger
from app.core.redis import redis_client
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Bypass rate limiting for test environments, documentation or asset endpoints
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/openapi.json") or path.startswith("/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        current_minute = int(time.time() / 60)

        # Format a unique redis key for the IP rate counter
        redis_key = f"rate:{client_ip}:{current_minute}"

        try:
            if redis_client.client:
                # Increment key. Use transaction or pipeline to set expire at same time.
                pipe = redis_client.client.pipeline()
                pipe.incr(redis_key)
                pipe.expire(redis_key, 60)
                results = await pipe.execute()

                request_count = results[0]

                if request_count > settings.RATE_LIMIT_PER_MINUTE:
                    logger.warning(
                        f"Rate limit exceeded for IP: {client_ip} "
                        f"(Requests: {request_count}/{settings.RATE_LIMIT_PER_MINUTE})"
                    )
                    return JSONResponse(
                        status_code=429,
                        content={
                            "success": False,
                            "message": "Too many requests. Please try again in a minute.",
                            "errors": [],
                        },
                    )
        except Exception as e:
            logger.error(f"Failed to resolve rate limit status from Redis: {e}")
            # In case of Redis failures, allow request to proceed (Fail-Open strategy)

        return await call_next(request)
