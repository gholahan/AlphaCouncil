"""API v1 endpoints package."""

from .documents import router as documents_router
from .health import router as health_router
from .analysis import router as analysis_router

__all__ = ["documents_router", "health_router", "analysis_router"]
