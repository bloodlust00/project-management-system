from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.redis import redis_client
from app.exceptions.handler import register_exception_handlers
from app.middlewares.logging_middleware import LoggingMiddleware
from app.middlewares.rate_limit_middleware import RateLimitMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events to manage resources like Redis connection pools on start and stop."""
    # Startup operations
    setup_logging()
    logger.info("Initializing backend services...")

    # Establish Redis connection
    redis_client.connect()

    yield

    # Shutdown operations
    logger.info("Stopping backend services...")
    await redis_client.disconnect()


# Instantiate FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Scalable Project Management System Enterprise REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register custom middlewares
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Apply CORS middleware last so it is executed first on request path
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exceptions formatter
register_exception_handlers(app)

# Include v1 endpoints router aggregator
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive Swagger documentation page."""
    return RedirectResponse(url="/docs")
