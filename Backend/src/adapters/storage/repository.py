"""Repository implementations using SQLModel."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from src.adapters.storage.models import (
    CompanyRecord,
    FinancialDocumentRecord,
    FinancialChunkRecord,
    DebateTraceRecord,
    DebateTurnRecord,
    UserRecord,
    WatchlistRecord,
)
from src.application.ports.outbound.repository import (
    CompanyRepository,
    DocumentRepository,
    DebateRepository,
    DebateTurnRepository,
    UserRepository,
    WatchlistRepository,
)


def _make_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# CompanyRepository
# ---------------------------------------------------------------------------
class SQLModelCompanyRepository(CompanyRepository):

    def __init__(self, database_url: str):
        self.async_session = _make_session_factory(database_url)

    async def create(self, ticker: str, company_data: Dict[str, Any]) -> None:
        async with self.async_session() as session:
            statement = select(CompanyRecord).where(CompanyRecord.ticker == ticker.upper())
            result = await session.execute(statement)
            existing = result.scalar_one_or_none()

            if existing:
                for key, value in company_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                company = CompanyRecord(
                    ticker=ticker.upper(),
                    name=company_data.get("name", ""),
                    sector=company_data.get("sector", ""),
                    ir_page_url=company_data.get("ir_page_url"),
                    is_preloaded=company_data.get("is_preloaded", False),
                )
                session.add(company)

            await session.commit()

    async def get_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(CompanyRecord).where(CompanyRecord.ticker == ticker.upper())
            result = await session.execute(statement)
            company = result.scalar_one_or_none()

            if not company:
                return None

            return {
                "id": str(company.id),
                "ticker": company.ticker,
                "name": company.name,
                "sector": company.sector,
                "ir_page_url": company.ir_page_url,
                "is_preloaded": company.is_preloaded,
                "last_ingestion_date": company.last_ingestion_date,
                "created_at": company.created_at,
            }

    async def list_all(self) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(CompanyRecord)
            result = await session.execute(statement)
            companies = result.scalars().all()

            return [
                {
                    "id": str(c.id),
                    "ticker": c.ticker,
                    "name": c.name,
                    "sector": c.sector,
                    "ir_page_url": c.ir_page_url,
                    "is_preloaded": c.is_preloaded,
                    "last_ingestion_date": c.last_ingestion_date,
                    "created_at": c.created_at,
                }
                for c in companies
            ]

    async def update_last_ingested(self, ticker: str, timestamp: datetime) -> None:
        async with self.async_session() as session:
            statement = select(CompanyRecord).where(CompanyRecord.ticker == ticker.upper())
            result = await session.execute(statement)
            company = result.scalar_one_or_none()

            if company:
                company.last_ingestion_date = timestamp
                await session.commit()


# ---------------------------------------------------------------------------
# DocumentRepository
# ---------------------------------------------------------------------------
class SQLModelDocumentRepository(DocumentRepository):

    def __init__(self, database_url: str):
        self.async_session = _make_session_factory(database_url)

    async def create(
        self,
        ticker: str,
        company_id: str,
        doc_type: str,
        fiscal_year: int,
        quarter: Optional[str] = None,
        source_url: Optional[str] = None,
        pdf_name: Optional[str] = None,
        total_chunks: int = 0,
        page_count: int = 0,
    ) -> str:
        async with self.async_session() as session:
            doc = FinancialDocumentRecord(
                company_id=UUID(company_id),
                ticker=ticker.upper(),
                doc_type=doc_type,
                fiscal_year=fiscal_year,
                quarter=quarter,
                source_url=source_url,
                pdf_name=pdf_name,
                total_chunks=total_chunks,
                page_count=page_count,
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            return str(doc.id)

    async def get_by_ticker(
        self,
        ticker: str,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(FinancialDocumentRecord).where(
                FinancialDocumentRecord.ticker == ticker.upper()
            )
            if doc_type:
                statement = statement.where(FinancialDocumentRecord.doc_type == doc_type)

            result = await session.execute(statement)
            docs = result.scalars().all()

            return [
                {
                    "id": str(d.id),
                    "company_id": str(d.company_id),
                    "ticker": d.ticker,
                    "doc_type": d.doc_type,
                    "fiscal_year": d.fiscal_year,
                    "quarter": d.quarter,
                    "source_url": d.source_url,
                    "pdf_name": d.pdf_name,
                    "total_chunks": d.total_chunks,
                    "page_count": d.page_count,
                    "ingested_at": d.ingested_at,
                }
                for d in docs
            ]

    async def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(FinancialDocumentRecord).where(
                FinancialDocumentRecord.id == UUID(document_id)
            )
            result = await session.execute(statement)
            d = result.scalar_one_or_none()

            if not d:
                return None

            return {
                "id": str(d.id),
                "company_id": str(d.company_id),
                "ticker": d.ticker,
                "doc_type": d.doc_type,
                "fiscal_year": d.fiscal_year,
                "quarter": d.quarter,
                "source_url": d.source_url,
                "pdf_name": d.pdf_name,
                "total_chunks": d.total_chunks,
                "page_count": d.page_count,
                "ingested_at": d.ingested_at,
            }

    async def exists(
        self,
        ticker: str,
        doc_type: str,
        fiscal_year: int,
        quarter: Optional[str] = None,
    ) -> bool:
        async with self.async_session() as session:
            statement = select(FinancialDocumentRecord).where(
                FinancialDocumentRecord.ticker == ticker.upper(),
                FinancialDocumentRecord.doc_type == doc_type,
                FinancialDocumentRecord.fiscal_year == fiscal_year,
            )
            if quarter:
                statement = statement.where(FinancialDocumentRecord.quarter == quarter)

            result = await session.execute(statement)
            return result.scalar_one_or_none() is not None

    async def update_chunk_count(self, document_id: str, total_chunks: int) -> None:
        async with self.async_session() as session:
            statement = select(FinancialDocumentRecord).where(
                FinancialDocumentRecord.id == UUID(document_id)
            )
            result = await session.execute(statement)
            doc = result.scalar_one_or_none()

            if doc:
                doc.total_chunks = total_chunks
                await session.commit()


# ---------------------------------------------------------------------------
# DebateRepository
# ---------------------------------------------------------------------------
class SQLModelDebateRepository(DebateRepository):

    def __init__(self, database_url: str):
        self.async_session = _make_session_factory(database_url)

    async def create(self, debate_data: Dict[str, Any]) -> str:
        async with self.async_session() as session:
            debate = DebateTraceRecord(
                ticker=debate_data["ticker"].upper(),
                company_id=UUID(debate_data["company_id"]) if debate_data.get("company_id") else None,
                user_id=UUID(debate_data["user_id"]) if debate_data.get("user_id") else None,
                user_thesis=debate_data.get("user_thesis"),
                capital_to_deploy=debate_data["capital_to_deploy"],
                risk_tolerance=debate_data["risk_tolerance"],
                transcript=[],
            )
            session.add(debate)
            await session.commit()
            await session.refresh(debate)
            return str(debate.id)

    async def get_by_id(self, debate_id: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(DebateTraceRecord).where(
                DebateTraceRecord.id == UUID(debate_id)
            )
            result = await session.execute(statement)
            debate = result.scalar_one_or_none()

            if not debate:
                return None

            return {
                "id": str(debate.id),
                "ticker": debate.ticker,
                "company_id": str(debate.company_id) if debate.company_id else None,
                "user_id": str(debate.user_id) if debate.user_id else None,
                "user_thesis": debate.user_thesis,
                "capital_to_deploy": debate.capital_to_deploy,
                "risk_tolerance": debate.risk_tolerance,
                "transcript": debate.transcript,
                "verdict": debate.verdict,
                "recommendation": debate.recommendation,
                "created_at": debate.created_at,
            }

    async def update_status(self, debate_id: str, status: str) -> None:
        pass

    async def save_verdict(self, debate_id: str, verdict: Dict[str, Any]) -> None:
        async with self.async_session() as session:
            statement = select(DebateTraceRecord).where(
                DebateTraceRecord.id == UUID(debate_id)
            )
            result = await session.execute(statement)
            debate = result.scalar_one_or_none()

            if debate:
                debate.verdict = verdict.get("verdict")
                debate.recommendation = verdict.get("recommendation")
                if verdict.get("transcript"):
                    debate.transcript = verdict["transcript"]
                    flag_modified(debate, "transcript")
                await session.commit()

    async def append_turn(
        self,
        debate_id: str,
        turn_number: int,
        agent_role: str,
        message: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        async with self.async_session() as session:
            statement = select(DebateTraceRecord).where(
                DebateTraceRecord.id == UUID(debate_id)
            )
            result = await session.execute(statement)
            debate = result.scalar_one_or_none()

            if debate:
                turn = {
                    "turn": turn_number,
                    "role": agent_role,
                    "content": message,
                    "tool_calls": tool_calls or [],
                }
                current = list(debate.transcript or [])
                current.append(turn)
                debate.transcript = current
                flag_modified(debate, "transcript")
                await session.commit()

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(DebateTraceRecord).where(
                DebateTraceRecord.user_id == UUID(user_id)
            ).limit(limit).offset(offset).order_by(DebateTraceRecord.created_at.desc())
            result = await session.execute(statement)
            debates = result.scalars().all()

            return [
                {
                    "id": str(d.id),
                    "ticker": d.ticker,
                    "user_thesis": d.user_thesis,
                    "capital_to_deploy": d.capital_to_deploy,
                    "risk_tolerance": d.risk_tolerance,
                    "verdict": d.verdict,
                    "created_at": d.created_at,
                }
                for d in debates
            ]


# ---------------------------------------------------------------------------
# DebateTurnRepository
# ---------------------------------------------------------------------------
class SQLModelDebateTurnRepository(DebateTurnRepository):

    def __init__(self, database_url: str):
        self.async_session = _make_session_factory(database_url)

    async def create(
        self,
        debate_id: str,
        agent_role: str,
        turn_number: int,
        content: str,
        citations: Optional[List[str]] = None,
        tools_called: Optional[List[Dict[str, Any]]] = None,
        token_count: Optional[int] = None,
    ) -> str:
        async with self.async_session() as session:
            turn = DebateTurnRecord(
                debate_id=UUID(debate_id),
                agent_role=agent_role,
                turn_number=turn_number,
                content=content,
                citations=citations,
                tools_called=tools_called,
                token_count=token_count,
            )
            session.add(turn)
            await session.commit()
            await session.refresh(turn)
            return str(turn.id)

    async def create_many(self, debate_id: str, turns: List[Dict[str, Any]]) -> None:
        """Bulk insert all turns for a debate in a single session."""
        async with self.async_session() as session:
            for t in turns:
                session.add(DebateTurnRecord(
                    debate_id=UUID(debate_id),
                    agent_role=t["agent_role"],
                    turn_number=t["turn_number"],
                    content=t["content"],
                    citations=t.get("citations"),
                    tools_called=t.get("tools_called"),
                    token_count=t.get("token_count"),
                ))
            await session.commit()

    async def get_by_debate(self, debate_id: str) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(DebateTurnRecord).where(
                DebateTurnRecord.debate_id == UUID(debate_id)
            ).order_by(DebateTurnRecord.turn_number)
            result = await session.execute(statement)
            turns = result.scalars().all()

            return [
                {
                    "id": str(t.id),
                    "debate_id": str(t.debate_id),
                    "agent_role": t.agent_role,
                    "turn_number": t.turn_number,
                    "content": t.content,
                    "citations": t.citations,
                    "tools_called": t.tools_called,
                    "token_count": t.token_count,
                    "created_at": t.created_at,
                }
                for t in turns
            ]

    async def get_by_role(
        self,
        agent_role: str,
        ticker: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(DebateTurnRecord).where(
                DebateTurnRecord.agent_role == agent_role
            )

            if ticker:
                # Join with DebateTraceRecord to filter by ticker
                statement = (
                    select(DebateTurnRecord)
                    .join(DebateTraceRecord, DebateTurnRecord.debate_id == DebateTraceRecord.id)
                    .where(
                        DebateTurnRecord.agent_role == agent_role,
                        DebateTraceRecord.ticker == ticker.upper(),
                    )
                )

            statement = statement.limit(limit).order_by(DebateTurnRecord.created_at.desc())
            result = await session.execute(statement)
            turns = result.scalars().all()

            return [
                {
                    "id": str(t.id),
                    "debate_id": str(t.debate_id),
                    "agent_role": t.agent_role,
                    "turn_number": t.turn_number,
                    "content": t.content,
                    "citations": t.citations,
                    "token_count": t.token_count,
                    "created_at": t.created_at,
                }
                for t in turns
            ]


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------
class SQLModelUserRepository(UserRepository):

    def __init__(self, database_url: str):
        self.async_session = _make_session_factory(database_url)

    async def create(self, email: str, name: str, subscription_tier: str = "free") -> str:
        async with self.async_session() as session:
            user = UserRecord(
                email=email,
                name=name,
                subscription_tier=subscription_tier,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return str(user.id)

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(UserRecord).where(UserRecord.id == UUID(user_id))
            result = await session.execute(statement)
            user = result.scalar_one_or_none()

            if not user:
                return None

            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "subscription_tier": user.subscription_tier,
                "daily_quota_remaining": user.daily_quota_remaining,
                "created_at": user.created_at,
            }

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(UserRecord).where(UserRecord.email == email)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()

            if not user:
                return None

            return {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "subscription_tier": user.subscription_tier,
                "daily_quota_remaining": user.daily_quota_remaining,
                "created_at": user.created_at,
            }

    async def update_quota(self, user_id: str, remaining: int) -> None:
        async with self.async_session() as session:
            statement = select(UserRecord).where(UserRecord.id == UUID(user_id))
            result = await session.execute(statement)
            user = result.scalar_one_or_none()

            if user:
                user.daily_quota_remaining = remaining
                await session.commit()

    async def reset_daily_quotas(self) -> int:
        async with self.async_session() as session:
            statement = select(UserRecord)
            result = await session.execute(statement)
            users = result.scalars().all()

            count = 0
            for user in users:
                if user.subscription_tier == "premium":
                    user.daily_quota_remaining = 50
                else:
                    user.daily_quota_remaining = 5
                count += 1

            await session.commit()
            return count


# ---------------------------------------------------------------------------
# WatchlistRepository
# ---------------------------------------------------------------------------
class SQLModelWatchlistRepository(WatchlistRepository):

    def __init__(self, database_url: str):
        self.async_session = _make_session_factory(database_url)

    async def add(self, user_id: str, company_id: str, alert_preferences: Optional[Dict[str, Any]] = None) -> str:
        async with self.async_session() as session:
            prefs = alert_preferences or {}
            item = WatchlistRecord(
                user_id=UUID(user_id),
                company_id=UUID(company_id),
                alert_on_new_filing=prefs.get("alert_on_new_filing", True),
                alert_on_price_drop=prefs.get("alert_on_price_drop", False),
                price_drop_threshold=prefs.get("price_drop_threshold"),
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return str(item.id)

    async def remove(self, user_id: str, company_id: str) -> None:
        async with self.async_session() as session:
            statement = select(WatchlistRecord).where(
                WatchlistRecord.user_id == UUID(user_id),
                WatchlistRecord.company_id == UUID(company_id),
            )
            result = await session.execute(statement)
            item = result.scalar_one_or_none()

            if item:
                await session.delete(item)
                await session.commit()

    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(WatchlistRecord).where(
                WatchlistRecord.user_id == UUID(user_id)
            )
            result = await session.execute(statement)
            items = result.scalars().all()

            return [
                {
                    "id": str(w.id),
                    "user_id": str(w.user_id),
                    "company_id": str(w.company_id),
                    "alert_on_new_filing": w.alert_on_new_filing,
                    "alert_on_price_drop": w.alert_on_price_drop,
                    "price_drop_threshold": w.price_drop_threshold,
                    "added_at": w.added_at,
                }
                for w in items
            ]

    async def get_users_watching(self, company_id: str) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            statement = select(WatchlistRecord).where(
                WatchlistRecord.company_id == UUID(company_id)
            )
            result = await session.execute(statement)
            items = result.scalars().all()

            return [
                {
                    "id": str(w.id),
                    "user_id": str(w.user_id),
                    "company_id": str(w.company_id),
                    "alert_on_new_filing": w.alert_on_new_filing,
                    "alert_on_price_drop": w.alert_on_price_drop,
                    "added_at": w.added_at,
                }
                for w in items
            ]
