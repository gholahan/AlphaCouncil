"""Analysis API endpoints - MAD debate with integrated RAG retrieval."""

from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult
from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.celery.tasks import run_investment_debate
from src.adapters.celery.app import celery_app
from src.adapters.storage.database import get_session
from src.adapters.storage.models import UserRecord
from src.entrypoints.api.dependencies import get_current_user
from src.config.settings import settings
from src.entrypoints.api.v1.schemas.analysis import (
    RunDebateRequest,
    StartDebateResponse,
    DebateTaskStatusResponse,
    GetDebateResponse,
)


router = APIRouter(tags=["Analysis & Debate"])


@router.post("/debate", response_model=StartDebateResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_debate(
    request: RunDebateRequest,
    current_user: UserRecord = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Start MAD (Multi agent Debate) investment analysis in background.

    Pipeline (runs async via Celery):
    1. Query financial data via RAG (automatic, internal)
    2. Run multi-round debate (Bull → Bear → Arbitrator)
    3. Generate investment verdict and recommendation
    4. Save full transcript to database

    Returns immediately with task_id for status tracking.
    Use GET /api/v1/analysis/debate/status/{task_id} to check progress.
    """
    try:
        # Check quota
        if current_user.daily_quota_remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily analysis quota exhausted. Upgrade to premium for unlimited debates.",
            )

        # Validate risk tolerance
        valid_risk_levels = ["conservative", "moderate", "aggressive"]
        if request.risk_tolerance.lower() not in valid_risk_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk_tolerance. Must be one of: {valid_risk_levels}"
            )

        # Deduct quota
        current_user.daily_quota_remaining -= 1
        session.add(current_user)
        await session.commit()

        # Start Celery background task
        task = run_investment_debate.delay(
            ticker=request.ticker.upper(),
            user_thesis=request.user_thesis,
            capital_to_deploy=request.capital_to_deploy,
            risk_tolerance=request.risk_tolerance,
            current_price=request.current_price,
            max_rounds=request.max_rounds,
        )

        return StartDebateResponse(
            task_id=task.id,
            ticker=request.ticker.upper(),
            user_thesis=request.user_thesis,
            capital_to_deploy=request.capital_to_deploy,
            risk_tolerance=request.risk_tolerance,
            current_price=request.current_price,
            max_rounds=request.max_rounds,
            status="PENDING",
            message=f"MAD debate started for {request.ticker.upper()} - RAG retrieval + multi-round analysis in progress",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start debate: {str(e)}"
        )


@router.get("/debate/status/{task_id}", response_model=DebateTaskStatusResponse)
async def get_debate_status(
    task_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Check status of a debate task.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = DebateTaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
        )

        if task_result.successful():
            response.result = task_result.result
        elif task_result.failed():
            response.error = str(task_result.info)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task status: {str(e)}"
        )


@router.get("/debate/{debate_id}", response_model=GetDebateResponse)
async def get_debate(
    debate_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Retrieve a saved debate by ID.
    """
    try:
        debate_repo = SQLModelDebateRepository(database_url=settings.DATABASE_URL)
        debate = await debate_repo.get_by_id(debate_id)

        if not debate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Debate {debate_id} not found"
            )

        return GetDebateResponse(**debate)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve debate: {str(e)}"
        )
