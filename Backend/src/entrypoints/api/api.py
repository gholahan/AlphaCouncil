"""Main API router that registers all endpoint groups."""

from fastapi import APIRouter
from src.entrypoints.api.v1.router import api_router as v1_router

# Create main API router
api_router = APIRouter()

# Register v1 router
api_router.include_router(v1_router, prefix="/api/v1")
