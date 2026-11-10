"""Debate API Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class DebateRequest(BaseModel):
    """Request schema for initiating an investment debate."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g. DANGCEM)")
    user_thesis: Optional[str] = Field(None, description="Optional investor thesis")
    capital: float = Field(10_000_000.0, description="Capital to deploy in NGN")
    risk_tolerance: str = Field("Moderate", description="Risk tolerance (Conservative, Moderate, Aggressive)")
    current_price: Optional[float] = Field(None, description="Current market price per share")


class DebateResponse(BaseModel):
    """Response schema for investment debate results."""

    ticker: str
    bull_case: Optional[str]
    bear_case: Optional[str]
    verdict: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
