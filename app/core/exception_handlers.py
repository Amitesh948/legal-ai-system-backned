"""
Legal AI System - Global Exception Handlers
=============================================
Registers FastAPI exception handlers for consistent error responses.
"""

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import LegalAIException

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    message: str,
    errors: list = None,
) -> dict:
    """Create a standardized error response envelope."""
    return {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(LegalAIException)
    async def legal_ai_exception_handler(request: Request, exc: LegalAIException):
        """Handle all custom LegalAI exceptions."""
        logger.warning(
            "LegalAIException: %s | Path: %s | Status: %d",
            exc.message,
            request.url.path,
            exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                status_code=exc.status_code,
                message=exc.message,
                errors=exc.errors,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic/FastAPI validation errors."""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            errors.append({
                "field": field,
                "message": error.get("msg", "Invalid value"),
            })

        logger.warning(
            "Validation error on %s: %s",
            request.url.path,
            errors,
        )
        return JSONResponse(
            status_code=422,
            content=create_error_response(
                status_code=422,
                message="Validation failed",
                errors=errors,
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for unhandled exceptions."""
        logger.exception(
            "Unhandled exception on %s: %s",
            request.url.path,
            str(exc),
        )
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                status_code=500,
                message="Internal server error" if not get_settings().is_development else str(exc),
            ),
        )


# Avoid circular import — lazy import
def get_settings():
    from app.config import get_settings as _get_settings
    return _get_settings()
