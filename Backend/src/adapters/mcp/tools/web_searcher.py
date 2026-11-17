"""MCP Web Search Tool - LangGraph-compatible tool for Tavily search with rich citation metadata."""

from typing import Dict, Any, Optional
from langchain_core.tools import tool
from src.adapters.web_search.tavily_client import TavilySearchAdapter


_search_adapter: Optional[TavilySearchAdapter] = None


def get_search_adapter() -> TavilySearchAdapter:
    global _search_adapter
    if _search_adapter is None:
        _search_adapter = TavilySearchAdapter()
    return _search_adapter


@tool
async def web_search_financial_context(
    query: str,
    ticker: Optional[str] = None,
    days_back: int = 7
) -> str:
    """
    Search the web for recent financial news and context about a company or topic.
    Returns results with complete source publisher domains, URLs, publication dates, and snippets.

    Args:
        query: What to search for (e.g., "earnings report", "CEO change", "debt refinancing")
        ticker: Stock ticker to focus the search (e.g., "DANGCEM")
        days_back: How many days back to search (default 7)

    Returns:
        Formatted search results with [WEB:n] citation markers, exact URLs, and publishers.
    """
    adapter = get_search_adapter()
    search_query = f"{ticker} {query}" if ticker else query

    results = await adapter.search_news(
        query=search_query,
        max_results=5,
        days_back=days_back,
    )

    formatted_output = [f"Search query: {search_query}\n"]
    formatted_output.append(f"Found {len(results)} verified web results:\n")

    for idx, res in enumerate(results, start=1):
        pub_date = f" | Date: {res.published_date}" if res.published_date else ""
        score_str = f" | Relevance: {res.relevance_score:.3f}" if res.relevance_score else ""
        formatted_output.append(f"\n[WEB:{idx}] {res.title}")
        formatted_output.append(f"Source Publisher: {res.source}{pub_date}{score_str}")
        formatted_output.append(f"URL: {res.url}")
        formatted_output.append(f"Content: \"{res.snippet}\"\n")

    return "\n".join(formatted_output)
