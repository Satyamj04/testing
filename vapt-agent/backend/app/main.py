"""
VAPT Agent - FastAPI Application Entrypoint
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging import configure_logging
from app.core.websocket_manager import ws_manager
from app.api.v1.router import api_router

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    logger.info("vapt_agent_starting", version="1.0.0", env=settings.APP_ENV)
    # Initialize MinIO buckets
    try:
        from app.core.storage import storage_client
        await storage_client.initialize_buckets()
    except Exception as e:
        logger.warning("storage_init_failed", error=str(e))
    yield
    logger.info("vapt_agent_stopping")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VAPT Agent",
        description="AI-Powered Vulnerability Assessment and Penetration Testing Platform",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(api_router, prefix="/api/v1")

    # WebSocket endpoint
    from app.api.v1.websocket import router as ws_router
    app.include_router(ws_router)

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_application()
