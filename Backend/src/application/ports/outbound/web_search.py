"""Web Search Port - Abstract interface for web search providers."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebSearchResult:
    """Single web search result."""

    title: str
    url: str
    snippet: str
    published_date: Optional[datetime] = None
    source: Optional[str] = None
    relevance_score: Optional[float] = None


class WebSearchClient(ABC):
    """Abstract base class for web search providers (Tavily, SerpAPI, etc.)."""

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[WebSearchResult]:
        """
        Perform a web search.

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def search_news(
        self,
        query: str,
        max_results: int = 10,
        days_back: int = 7,
    ) -> List[WebSearchResult]:
        """
        Search recent news articles.

        Returns:
            List of news search results
        """
        pass

    @abstractmethod
    async def extract_content(self, url: str) -> str:
        """
        Extract clean text content from a URL.

        Args:
            url: URL to extract content from

        Returns:
            Extracted text content
        """
        pass
