"""Document API Schemas - Request/Response models for ingestion endpoints."""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class IngestDocumentRequest(BaseModel):
    """Request body for document ingestion."""

    ticker: str = Field(..., description="Company ticker symbol", min_length=1, max_length=10)
    pdf_url: HttpUrl = Field(..., description="URL to download PDF from")
    filing_type: str = Field(..., description="Document type: annual_report, quarterly, or news")
    fiscal_year: int = Field(..., description="Fiscal year of the document", ge=2000, le=2050)
    quarter: Optional[str] = Field(None, description="Quarter: Q1, Q2, Q3, or Q4 (for quarterly reports)")


class IngestDocumentResponse(BaseModel):
    """Response from document ingestion request."""

    task_id: str = Field(..., description="Celery task ID for tracking status")
    ticker: str
    filing_type: str
    fiscal_year: int
    quarter: Optional[str]
    status: str = Field(default="PENDING", description="Initial task status")
    message: str = Field(default="Document ingestion started")


class TaskStatusResponse(BaseModel):
    """Response for task status check."""

    task_id: str
    status: str = Field(..., description="PENDING, STARTED, SUCCESS, FAILURE, RETRY")
    result: Optional[dict] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
