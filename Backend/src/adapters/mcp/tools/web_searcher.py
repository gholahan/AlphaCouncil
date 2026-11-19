"""MCP Web Search Tool - LangGraph-compatible tool for Tavily search with clean citation formatting."""

from typing import Optional
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
    Returns results with clean URLs and snippet content.

    Args:
        query: What to search for (e.g., "earnings report", "CEO change", "debt refinancing")
        ticker: Stock ticker to focus the search (e.g., "DANGCEM")
        days_back: How many days back to search (default 7)

    Returns:
        Formatted search results with ChatGPT-style markers [1], [2], clean URLs, and snippets.
    """
    adapter = get_search_adapter()
    search_query = f"{ticker} {query}" if ticker else query

    results = await adapter.search_news(
        query=search_query,
        max_results=5,
        days_back=days_back,
    )

    formatted_output = [f"Web search results for: {search_query}\n"]

    for idx, res in enumerate(results, start=1):
        formatted_output.append(f"[{idx}] {res.title}")
        formatted_output.append(f"URL: {res.url}")
        formatted_output.append(f"Snippet: \"{res.snippet}\"\n")

    return "\n".join(formatted_output)
