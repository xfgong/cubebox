"""FastAPI Application Factory

Creates and configures the FastAPI application with:
- Lifespan management (startup/shutdown)
- Middleware configuration
- Router registration
- Error handling
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from cubebox.utils import log


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # ==================== Startup ====================
    log.init()
    logger.info("Application starting up")

    yield

    # ==================== Shutdown ====================
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="cubebox API",
        description="AI Agent System Backend with DeepAgents Framework",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register routers
    # TODO: Add routers as they are implemented
    # from cubebox.api.routes import api_router
    # app.include_router(api_router)

    return app
