"""Company API Schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class CompanyCreate(BaseModel):
    """Schema for registering a company."""

    ticker: str = Field(..., max_length=10)
    name: str = Field(..., max_length=100)
    sector: str = Field(..., max_length=50)
    ir_page_url: Optional[str] = None
    is_preloaded: bool = False


class CompanyResponse(BaseModel):
    """Schema for company response."""

    id: str
    ticker: str
    name: str
    sector: str
    ir_page_url: Optional[str] = None
    is_preloaded: bool = False
    last_ingestion_date: Optional[str] = None
