"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.logging import setup_logging_from_settings, get_logger
from src.config.settings import settings
from src.entrypoints.api.api import api_router

# Initialize centralized logging first
setup_logging_from_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"API prefix: {settings.API_V1_PREFIX}")

    yield

    # Shutdown
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.APP_NAME,
    description="AlphaCouncil - AI-Powered Investment Analysis for Nigerian Stocks",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(api_router)
