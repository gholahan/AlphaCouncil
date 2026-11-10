"""Document ingestion API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from celery.result import AsyncResult

from src.adapters.celery.tasks import ingest_pdf_document
from src.adapters.celery.app import celery_app
from src.adapters.storage.models import UserRecord
from src.entrypoints.api.dependencies import get_current_user
from src.entrypoints.api.v1.schemas.documents import (
    IngestDocumentRequest,
    IngestDocumentResponse,
    TaskStatusResponse,
)


router = APIRouter(tags=["Documents"])


@router.post("/ingest", response_model=IngestDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    request: IngestDocumentRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Start background ingestion of a company financial document.

    Pipeline:
    1. Download PDF from URL
    2. Extract text page-by-page
    3. Chunk text (2000 chars, 200 overlap)
    4. Generate embeddings (Voyage AI voyage-finance-2)
    5. Store in pgvector with metadata
    6. Update company.last_ingestion_date

    Returns immediately with task_id for status tracking.
    """
    try:
        # Validate filing_type
        valid_types = ["annual_report", "quarterly", "news"]
        if request.filing_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filing_type. Must be one of: {valid_types}"
            )

        # Validate quarter for quarterly reports
        if request.filing_type == "quarterly" and not request.quarter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="quarter is required for quarterly reports"
            )

        if request.quarter and request.quarter not in ["Q1", "Q2", "Q3", "Q4"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="quarter must be one of: Q1, Q2, Q3, Q4"
            )

        # Start Celery task
        task = ingest_pdf_document.delay(
            ticker=request.ticker.upper(),
            pdf_url=str(request.pdf_url),
            filing_type=request.filing_type,
            fiscal_year=request.fiscal_year,
            quarter=request.quarter,
        )

        return IngestDocumentResponse(
            task_id=task.id,
            ticker=request.ticker.upper(),
            filing_type=request.filing_type,
            fiscal_year=request.fiscal_year,
            quarter=request.quarter,
            status="PENDING",
            message=f"Document ingestion started for {request.ticker.upper()} - {request.filing_type} FY{request.fiscal_year}",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ingestion task: {str(e)}"
        )


@router.get("/ingest/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Check status of a document ingestion task.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = TaskStatusResponse(
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
