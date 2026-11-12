"""Database Models - All SQLModel tables for AlphaCouncil."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4
from pgvector.sqlalchemy import Vector
from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy import ForeignKey, UniqueConstraint, Text
from typing import Optional, List


# ---------------------------------------------------------------------------
# 1. UserRecord
# ---------------------------------------------------------------------------
class UserRecord(SQLModel, table=True):
    """System user (authentication & rate limiting)."""
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    name: str = Field(max_length=150)
    subscription_tier: str = Field(default="free", max_length=20)  # "free", "premium"
    daily_quota_remaining: int = Field(default=5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 2. CompanyRecord
# ---------------------------------------------------------------------------
class CompanyRecord(SQLModel, table=True):
    """Tracked companies on the Nigerian Exchange (NGX)."""
    __tablename__ = "companies"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticker: str = Field(index=True, unique=True, max_length=10)
    name: str = Field(max_length=100)
    sector: str = Field(max_length=50)
    ir_page_url: str | None = Field(default=None)
    is_preloaded: bool = Field(default=False)
    last_ingestion_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 3. FinancialDocumentRecord
# ---------------------------------------------------------------------------
class FinancialDocumentRecord(SQLModel, table=True):
    """A single ingested financial document (PDF)."""
    __tablename__ = "financial_documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    company_id: UUID = Field(
        sa_column_kwargs={"nullable": False},
        foreign_key="companies.id",
        index=True,
    )
    ticker: str = Field(index=True, max_length=10)
    doc_type: str = Field(max_length=30)  # "annual_report", "quarterly", "investor_presentation", "news"
    fiscal_year: int
    quarter: str | None = Field(default=None, max_length=5)  # "Q1"-"Q4"
    source_url: str | None = Field(default=None, sa_column=Column(Text))
    pdf_name: str | None = Field(default=None, max_length=255)
    total_chunks: int = Field(default=0)
    page_count: int = Field(default=0)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 4. FinancialChunkRecord
# ---------------------------------------------------------------------------
class FinancialChunkRecord(SQLModel, table=True):
    """Embedded chunk of text from a financial document (core RAG table).

    Uses pgvector for similarity search against query embeddings.
    """
    __tablename__ = "financial_chunks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticker: str = Field(index=True, max_length=10)
    company_id: UUID | None = Field(default=None, foreign_key="companies.id", index=True)
    document_id: UUID | None = Field(default=None, foreign_key="financial_documents.id", index=True)

    # Document metadata
    filing_type: str = Field(max_length=20)  # "annual_report", "quarterly", "news"
    fiscal_year: int | None = Field(default=None, index=True)
    quarter: str | None = Field(default=None, max_length=5)
    section: str | None = Field(default=None, max_length=100)  # "MD&A", "Balance Sheet"
    chunk_index: int

    # Content & Vector (1024 dimensions for Voyage AI voyage-finance-2)
    chunk_text: str = Field(sa_column=Column(Text))
    embedding: list[float] = Field(
        sa_column=Column(Vector(1024))
    )

    # Flexible metadata (page_number, pdf_name, page_range, char_start, char_end)
    metadata_json: dict = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 5. DebateTraceRecord
# ---------------------------------------------------------------------------
class DebateTraceRecord(SQLModel, table=True):
    """Full investment committee debate (audit trail)."""
    __tablename__ = "debate_traces"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticker: str = Field(index=True, max_length=10)
    company_id: UUID | None = Field(default=None, foreign_key="companies.id", index=True)
    user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True)
    user_thesis: str | None = Field(default=None, sa_column=Column(Text))
    capital_to_deploy: float
    risk_tolerance: str = Field(max_length=20)

    # Full transcript as JSON array of turns
    transcript: list[dict] = Field(default=[], sa_column=Column(JSON))

    # Final verdict and structured recommendation
    verdict: str | None = Field(default=None, max_length=30)
    recommendation: dict | None = Field(default=None, sa_column=Column(JSON))
    chat_response: str | None = Field(default=None, sa_column=Column(Text))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 6. DebateTurnRecord
# ---------------------------------------------------------------------------
class DebateTurnRecord(SQLModel, table=True):
    """A single turn within a debate (one agent's output)."""
    __tablename__ = "debate_turns"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    debate_id: UUID = Field(foreign_key="debate_traces.id", index=True)
    agent_role: str = Field(max_length=30)  # "bull_analyst", "bear_analyst", "arbitrator"
    turn_number: int
    content: str = Field(sa_column=Column(Text))
    citations: list | None = Field(default=None, sa_column=Column(JSON))  # ["[REF:1]", "[WEB:2]"]
    tools_called: list | None = Field(default=None, sa_column=Column(JSON))
    token_count: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 7. WatchlistRecord
# ---------------------------------------------------------------------------
class WatchlistRecord(SQLModel, table=True):
    """User's saved watchlist of stocks to track."""
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_company_watchlist"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    company_id: UUID = Field(foreign_key="companies.id", index=True)
    alert_on_new_filing: bool = Field(default=True)
    alert_on_price_drop: bool = Field(default=False)
    price_drop_threshold: float | None = Field(default=None)  # e.g. 5.0 for 5% drop
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
