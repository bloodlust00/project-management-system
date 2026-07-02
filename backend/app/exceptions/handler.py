from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions.custom import BaseAppException
from app.core.logging import logger

def register_exception_handlers(app: FastAPI) -> None:
    """Registers exception handlers to standard JSON structures."""

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException):
        """Intercepts internal base app exceptions."""
        logger.warning(f"App exception: {exc.message} (status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "errors": exc.errors
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Intercepts Pydantic validation errors and reformats them."""
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error.get("loc", []))
            errors.append({
                "field": loc,
                "message": error.get("msg"),
                "type": error.get("type")
            })
        
        logger.warning(f"Validation failed for path {request.url.path}: {errors}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Validation failed",
                "errors": errors
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """Intercepts low-level database operations exceptions."""
        logger.error(f"SQLAlchemy database failure: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "A database error occurred while processing the request.",
                "errors": []
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Intercepts all unhandled python system exceptions."""
        logger.critical(f"Unhandled exception caught on request path {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected server error occurred.",
                "errors": []
            }
        )
