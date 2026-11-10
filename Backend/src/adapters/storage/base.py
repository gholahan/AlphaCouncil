"""Base - Import all models so Alembic autogenerate detects every table."""

from src.adapters.storage.models import (  # noqa: F401
    CompanyRecord,
    FinancialDocumentRecord,
    FinancialChunkRecord,
    DebateTraceRecord,
    DebateTurnRecord,
    UserRecord,
    WatchlistRecord,
)
from sqlmodel import SQLModel

metadata = SQLModel.metadata
