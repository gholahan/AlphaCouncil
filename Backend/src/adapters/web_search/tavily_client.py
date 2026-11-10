from typing import List, Optional, Dict, Any
from datetime import datetime
from tavily import TavilyClient

from src.application.ports.outbound.web_search import WebSearchClient, WebSearchResult
from src.config.settings import settings


class TavilySearchAdapter(WebSearchClient):
    """Adapter for Tavily AI search API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TAVILY_API_KEY

        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required for TavilySearchAdapter")
        self.client = TavilyClient(api_key=self.api_key)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[WebSearchResult]:
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )

            results = []
            for item in response.get("results", []):
                results.append(
                    WebSearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        published_date=None,
                        source=item.get("url", "").split("/")[2] if "url" in item else None,
                        relevance_score=item.get("score"),
                    )
                )
            return results
        except Exception as e:
            raise RuntimeError(f"Tavily search failed for query '{query}': {str(e)}")

    async def search_news(
        self,
        query: str,
        max_results: int = 5,
        days_back: int = 7,
    ) -> List[WebSearchResult]:
        news_query = f"{query} financial news Nigeria stock market"
        return await self.search(
            query=news_query,
            max_results=max_results,
            search_depth="advanced",
        )

    async def extract_content(self, url: str) -> str:
        try:
            response = self.client.extract(urls=[url])
            results = response.get("results", [])
            if results:
                return results[0].get("raw_content", "")
            return ""
        except Exception as e:
            raise RuntimeError(f"Tavily content extraction failed for {url}: {str(e)}")
