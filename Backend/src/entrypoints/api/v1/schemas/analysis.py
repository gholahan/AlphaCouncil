"""Analysis API Schemas - Request/Response models for MAD debate endpoints."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class RunDebateRequest(BaseModel):
    """Request body for triggering MAD debate."""

    ticker: str = Field(..., description="Company ticker symbol", min_length=1, max_length=10)
    user_thesis: Optional[str] = Field(None, description="Optional user's investment thesis")
    capital_to_deploy: float = Field(default=1000000.0, description="Capital to deploy (NGN)", gt=0)
    risk_tolerance: str = Field(default="moderate", description="Risk tolerance: conservative, moderate, aggressive")
    current_price: Optional[float] = Field(None, description="Current stock price (NGN)", gt=0)
    max_rounds: int = Field(default=3, description="Maximum debate rounds", ge=1, le=5)

    @field_validator("risk_tolerance")
    @classmethod
    def validate_and_normalize_risk_tolerance(cls, v: str) -> str:
        if not v:
            return "Moderate"
        normalized = v.strip().capitalize()
        if normalized not in {"Conservative", "Moderate", "Aggressive"}:
            raise ValueError(f"Invalid risk tolerance: '{v}'. Must be conservative, moderate, or aggressive.")
        return normalized


class StartDebateResponse(BaseModel):
    """Response when debate task is started."""

    task_id: str
    ticker: str
    user_thesis: Optional[str]
    capital_to_deploy: float
    risk_tolerance: str
    current_price: Optional[float]
    max_rounds: int
    status: str = Field(default="PENDING", description="Initial task status")
    message: str


class DebateTaskStatusResponse(BaseModel):
    """Response for debate task status check."""

    task_id: str
    status: str = Field(description="PENDING, STARTED, SUCCESS, FAILURE")
    result: Optional[Dict[str, Any]] = Field(None, description="Full debate result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class GetDebateResponse(BaseModel):
    """Response for retrieving saved debate."""

    id: str
    ticker: str
    user_thesis: Optional[str]
    capital_to_deploy: float
    risk_tolerance: str
    transcript: List[Dict[str, Any]]
    verdict: Optional[str]
    recommendation: Optional[Dict[str, Any]]
    created_at: datetime
