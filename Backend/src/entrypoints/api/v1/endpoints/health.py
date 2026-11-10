from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for API v1."""
    return {"status": "healthy", "version": "1.0.0"}
