"""Repository Port - Abstract interfaces for data persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class DebateRepository(ABC):
    """Abstract repository for debate persistence."""

    @abstractmethod
    async def create(self, debate_data: Dict[str, Any]) -> str:
        """Create a new debate record. Returns debate ID."""
        pass

    @abstractmethod
    async def get_by_id(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a debate by ID."""
        pass

    @abstractmethod
    async def update_status(self, debate_id: str, status: str) -> None:
        """Update debate status ('pending', 'running', 'completed', 'failed')."""
        pass

    @abstractmethod
    async def save_verdict(self, debate_id: str, verdict: Dict[str, Any]) -> None:
        """Save final investment verdict for a debate."""
        pass

    @abstractmethod
    async def append_turn(
        self,
        debate_id: str,
        turn_number: int,
        agent_role: str,
        message: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Append a debate turn to the transcript."""
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List debates for a user."""
        pass


class CompanyRepository(ABC):
    """Abstract repository for company/ticker metadata."""

    @abstractmethod
    async def create(self, ticker: str, company_data: Dict[str, Any]) -> None:
        """Create or update company record."""
        pass

    @abstractmethod
    async def get_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company by ticker."""
        pass

    @abstractmethod
    async def list_all(self) -> List[Dict[str, Any]]:
        """List all companies in the system."""
        pass

    @abstractmethod
    async def update_last_ingested(self, ticker: str, timestamp: datetime) -> None:
        """Update the last ingestion timestamp for a company."""
        pass


class DocumentRepository(ABC):
    """Abstract repository for financial documents."""

    @abstractmethod
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
        """Create a document record. Returns document ID."""
        pass

    @abstractmethod
    async def get_by_ticker(
        self,
        ticker: str,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get documents for a ticker, optionally filtered by type."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        pass

    @abstractmethod
    async def exists(
        self,
        ticker: str,
        doc_type: str,
        fiscal_year: int,
        quarter: Optional[str] = None,
    ) -> bool:
        """Check if a document has already been ingested (dedup)."""
        pass

    @abstractmethod
    async def update_chunk_count(self, document_id: str, total_chunks: int) -> None:
        """Update the total chunk count after ingestion completes."""
        pass


class DebateTurnRepository(ABC):
    """Abstract repository for individual debate turns (normalized)."""

    @abstractmethod
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
        """Create a debate turn record. Returns turn ID."""
        pass

    @abstractmethod
    async def get_by_debate(self, debate_id: str) -> List[Dict[str, Any]]:
        """Get all turns for a debate, ordered by turn_number."""
        pass

    @abstractmethod
    async def get_by_role(
        self,
        agent_role: str,
        ticker: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get turns by agent role (e.g. all bear cases for banking stocks)."""
        pass


class UserRepository(ABC):
    """Abstract repository for user management."""

    @abstractmethod
    async def create(self, email: str, name: str, subscription_tier: str = "free") -> str:
        """Create a user. Returns user ID."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        pass

    @abstractmethod
    async def update_quota(self, user_id: str, remaining: int) -> None:
        """Update daily quota remaining."""
        pass

    @abstractmethod
    async def reset_daily_quotas(self) -> int:
        """Reset all users' daily quotas. Returns count of users reset."""
        pass


class WatchlistRepository(ABC):
    """Abstract repository for user watchlists."""

    @abstractmethod
    async def add(self, user_id: str, company_id: str, alert_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Add a company to user's watchlist. Returns watchlist entry ID."""
        pass

    @abstractmethod
    async def remove(self, user_id: str, company_id: str) -> None:
        """Remove a company from user's watchlist."""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all watchlist items for a user."""
        pass

    @abstractmethod
    async def get_users_watching(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all users watching a specific company (for notifications)."""
        pass


class MacroIndicatorRepository(ABC):
    """Abstract repository for macro-economic indicators (CBN rates, inflation, etc.)."""

    @abstractmethod
    async def get_latest_cbn_rates(self) -> Optional[Dict[str, Any]]:
        """Get the most recent CBN monetary policy rates."""
        pass

    @abstractmethod
    async def upsert_cbn_rates(self, rates: Dict[str, Any]) -> None:
        """Insert or update CBN rates record."""
        pass
