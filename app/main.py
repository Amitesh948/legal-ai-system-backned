"""
Legal AI System - FastAPI Application Factory
==============================================
Main entry point for the FastAPI application.
Configures middleware, exception handlers, and routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.api.v1.router import api_v1_router


def create_app() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered Legal Consultation & Case Management System",
        version="1.0.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json" if settings.is_development else None,
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Register Exception Handlers ---
    register_exception_handlers(app)

    # --- Register API Routes ---
    app.include_router(api_v1_router, prefix="/api/v1")

    # --- Serve Uploaded Files ---
    import os
    from fastapi.staticfiles import StaticFiles
    
    os.makedirs(settings.upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    # --- Health Check ---
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "environment": settings.app_env,
        }

    return app


# Create the application instance
app = create_app()
