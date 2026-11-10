"""API v1 Router - Aggregates all route modules."""

from fastapi import APIRouter

from src.entrypoints.api.v1.endpoints import health, companies, analysis, documents, auth

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis & Debate"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
