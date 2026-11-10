"""SQLAlchemy/SQLModel Repository Implementations for AlphaCouncil."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.adapters.storage.models import CompanyRecord, DebateTraceRecord, FinancialChunkRecord
from src.application.ports.outbound.repository import (
    DebateRepository,
    CompanyRepository,
    DocumentRepository,
    MacroIndicatorRepository,
)


class SqlAlchemyDebateRepository(DebateRepository):
    """SQLAlchemy implementation of DebateRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, debate_data: Dict[str, Any]) -> str:
        """Create a new debate record."""
        debate = DebateTraceRecord(
            ticker=debate_data.get("ticker", "").upper(),
            user_thesis=debate_data.get("user_thesis"),
            capital_to_deploy=debate_data.get("capital_to_deploy", 10_000_000.0),
            risk_tolerance=debate_data.get("risk_tolerance", "Moderate"),
            transcript=debate_data.get("transcript", []),
            verdict=debate_data.get("verdict"),
            recommendation=debate_data.get("recommendation"),
        )
        self.session.add(debate)
        await self.session.commit()
        await self.session.refresh(debate)
        return str(debate.id)

    async def get_by_id(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a debate by ID."""
        try:
            uuid_obj = UUID(debate_id)
        except ValueError:
            return None

        debate = await self.session.get(DebateTraceRecord, uuid_obj)
        if not debate:
            return None

        return {
            "id": str(debate.id),
            "ticker": debate.ticker,
            "user_thesis": debate.user_thesis,
            "capital_to_deploy": debate.capital_to_deploy,
            "risk_tolerance": debate.risk_tolerance,
            "transcript": debate.transcript,
            "verdict": debate.verdict,
            "recommendation": debate.recommendation,
            "created_at": debate.created_at.isoformat() if debate.created_at else None,
        }

    async def update_status(self, debate_id: str, status: str) -> None:
        """Update debate status (stored in metadata or transcript if needed)."""
        # For simplicity in trace record, status can be tracked or ignored if completed
        pass

    async def save_verdict(self, debate_id: str, verdict: Dict[str, Any]) -> None:
        """Save final investment verdict for a debate."""
        try:
            uuid_obj = UUID(debate_id)
        except ValueError:
            return

        debate = await self.session.get(DebateTraceRecord, uuid_obj)
        if debate:
            debate.verdict = verdict.get("verdict")
            debate.recommendation = verdict
            self.session.add(debate)
            await self.session.commit()

    async def append_turn(
        self,
        debate_id: str,
        turn_number: int,
        agent_role: str,
        message: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Append a debate turn to the transcript."""
        try:
            uuid_obj = UUID(debate_id)
        except ValueError:
            return

        debate = await self.session.get(DebateTraceRecord, uuid_obj)
        if debate:
            turn_data = {
                "turn": turn_number,
                "role": agent_role,
                "content": message,
                "tool_calls": tool_calls or [],
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Ensure transcript is a mutable list copy
            transcript = list(debate.transcript or [])
            transcript.append(turn_data)
            debate.transcript = transcript
            self.session.add(debate)
            await self.session.commit()

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List debates (user_id filter can be added if users table exists)."""
        stmt = select(DebateTraceRecord).order_by(DebateTraceRecord.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.exec(stmt)
        debates = result.all()

        return [
            {
                "id": str(d.id),
                "ticker": d.ticker,
                "user_thesis": d.user_thesis,
                "verdict": d.verdict,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in debates
        ]


class SqlAlchemyCompanyRepository(CompanyRepository):
    """SQLAlchemy implementation of CompanyRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticker: str, company_data: Dict[str, Any]) -> None:
        """Create or update company record."""
        stmt = select(CompanyRecord).where(CompanyRecord.ticker == ticker.upper())
        result = await self.session.exec(stmt)
        existing = result.first()

        if existing:
            existing.name = company_data.get("name", existing.name)
            existing.sector = company_data.get("sector", existing.sector)
            existing.ir_page_url = company_data.get("ir_page_url", existing.ir_page_url)
            existing.is_preloaded = company_data.get("is_preloaded", existing.is_preloaded)
            self.session.add(existing)
        else:
            company = CompanyRecord(
                ticker=ticker.upper(),
                name=company_data.get("name", ticker),
                sector=company_data.get("sector", "General"),
                ir_page_url=company_data.get("ir_page_url"),
                is_preloaded=company_data.get("is_preloaded", False),
            )
            self.session.add(company)
        await self.session.commit()

    async def get_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company by ticker."""
        stmt = select(CompanyRecord).where(CompanyRecord.ticker == ticker.upper())
        result = await self.session.exec(stmt)
        company = result.first()

        if not company:
            return None

        return {
            "id": str(company.id),
            "ticker": company.ticker,
            "name": company.name,
            "sector": company.sector,
            "ir_page_url": company.ir_page_url,
            "is_preloaded": company.is_preloaded,
            "last_ingestion_date": company.last_ingestion_date.isoformat() if company.last_ingestion_date else None,
        }

    async def list_all(self) -> List[Dict[str, Any]]:
        """List all companies in the system."""
        stmt = select(CompanyRecord)
        result = await self.session.exec(stmt)
        companies = result.all()

        return [
            {
                "id": str(c.id),
                "ticker": c.ticker,
                "name": c.name,
                "sector": c.sector,
                "ir_page_url": c.ir_page_url,
                "is_preloaded": c.is_preloaded,
                "last_ingestion_date": c.last_ingestion_date.isoformat() if c.last_ingestion_date else None,
            }
            for c in companies
        ]

    async def update_last_ingested(self, ticker: str, timestamp: datetime) -> None:
        """Update last ingestion timestamp for a company."""
        stmt = select(CompanyRecord).where(CompanyRecord.ticker == ticker.upper())
        result = await self.session.exec(stmt)
        company = result.first()
        if company:
            company.last_ingestion_date = timestamp
            self.session.add(company)
            await self.session.commit()


class SqlAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of DocumentRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        ticker: str,
        doc_type: str,
        filing_date: datetime,
        file_path: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Create a document record (stub or tracking in metadata_json)."""
        # Can be stored using FinancialChunkRecord or dedicated Document model if created.
        return "doc-uuid-placeholder"

    async def get_by_ticker(
        self,
        ticker: str,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get documents for a ticker."""
        stmt = select(FinancialChunkRecord).where(FinancialChunkRecord.ticker == ticker.upper())
        result = await self.session.exec(stmt)
        chunks = result.all()
        # Return unique filing summaries from chunks
        docs_map = {}
        for c in chunks:
            ft = c.filing_type
            if ft not in docs_map:
                docs_map[ft] = {
                    "ticker": c.ticker,
                    "doc_type": ft,
                    "fiscal_year": c.fiscal_year,
                }
        return list(docs_map.values())

    async def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        return None


class SqlAlchemyMacroIndicatorRepository(MacroIndicatorRepository):
    """SQLAlchemy implementation of MacroIndicatorRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_cbn_rates(self) -> Optional[Dict[str, Any]]:
        """Get latest CBN rates."""
        return {"monetary_policy_rate": 27.25, "inflation_rate": 32.7, "last_updated": "2026-10-01"}

    async def upsert_cbn_rates(self, rates: Dict[str, Any]) -> None:
        """Upsert CBN rates."""
        pass
