"""Companies endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List

from src.entrypoints.api.v1.schemas.company import CompanyCreate, CompanyResponse

router = APIRouter()

# In-memory storage for demonstration / fallback when DB is starting up
IN_MEMORY_COMPANIES = [
    {
        "id": "c1",
        "ticker": "DANGCEM",
        "name": "Dangote Cement Plc",
        "sector": "Industrial Goods",
        "ir_page_url": "https://www.dangotecement.com",
        "is_preloaded": True,
        "last_ingestion_date": "2026-10-01T00:00:00",
    },
    {
        "id": "c2",
        "ticker": "ZENITHBANK",
        "name": "Zenith Bank Plc",
        "sector": "Financial Services",
        "ir_page_url": "https://www.zenithbank.com",
        "is_preloaded": True,
        "last_ingestion_date": "2026-10-01T00:00:00",
    },
    {
        "id": "c3",
        "ticker": "MTNN",
        "name": "MTN Nigeria Communications Plc",
        "sector": "Telecommunications",
        "ir_page_url": "https://www.mtn.ng",
        "is_preloaded": True,
        "last_ingestion_date": "2026-10-01T00:00:00",
    },
]


@router.get("/", response_model=List[CompanyResponse])
async def list_companies():
    """List all tracked companies."""
    return IN_MEMORY_COMPANIES


@router.get("/{ticker}", response_model=CompanyResponse)
async def get_company(ticker: str):
    """Get company by ticker symbol."""
    for company in IN_MEMORY_COMPANIES:
        if company["ticker"].upper() == ticker.upper():
            return company
    raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
