"""Preload NGX companies script."""

import asyncio
import logging
from src.config.settings import settings
from src.adapters.storage.repository import SQLModelCompanyRepository

logger = logging.getLogger(__name__)

PRELOADED_COMPANIES = [
    {
        "ticker": "DANGCEM",
        "name": "Dangote Cement Plc",
        "sector": "Industrial Goods",
        "ir_page_url": "https://www.dangotecement.com",
        "is_preloaded": True,
    },
    {
        "ticker": "ZENITHBANK",
        "name": "Zenith Bank Plc",
        "sector": "Financial Services",
        "ir_page_url": "https://www.zenithbank.com",
        "is_preloaded": True,
    },
    {
        "ticker": "MTNN",
        "name": "MTN Nigeria Communications Plc",
        "sector": "Telecommunications",
        "ir_page_url": "https://www.mtn.ng",
        "is_preloaded": True,
    },
    {
        "ticker": "GTCO",
        "name": "Guaranty Trust Holding Company Plc",
        "sector": "Financial Services",
        "ir_page_url": "https://www.gtcoplc.com",
        "is_preloaded": True,
    },
    {
        "ticker": "BUACEMENT",
        "name": "BUA Cement Plc",
        "sector": "Industrial Goods",
        "ir_page_url": "https://www.buacement.com",
        "is_preloaded": True,
    },
    {
        "ticker": "ACCESSCORP",
        "name": "Access Holdings Plc",
        "sector": "Financial Services",
        "ir_page_url": "https://www.accessholdingsplc.com",
        "is_preloaded": True,
    },
    {
        "ticker": "SEPLAT",
        "name": "Seplat Energy Plc",
        "sector": "Oil & Gas",
        "ir_page_url": "https://seplatenergy.com",
        "is_preloaded": True,
    },
    {
        "ticker": "TRANSCORP",
        "name": "Transnational Corporation Plc",
        "sector": "Conglomerates",
        "ir_page_url": "https://transcorpplc.com",
        "is_preloaded": True,
    },
]


async def preload_companies():
    """Seed preloaded NGX companies into the database."""
    repo = SQLModelCompanyRepository(settings.DATABASE_URL)
    print(f"Seeding {len(PRELOADED_COMPANIES)} preloaded NGX companies...")
    for comp in PRELOADED_COMPANIES:
        await repo.create(comp["ticker"], comp)
        print(f" - Seeded {comp['ticker']} ({comp['name']})")
    print("Preload completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    if sys.platform == "win32":
        asyncio.run(preload_companies(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(preload_companies())
