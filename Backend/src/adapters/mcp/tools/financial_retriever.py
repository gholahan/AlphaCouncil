"""MCP Financial Retriever Tool - RAG search over financial documents."""

import time
from langchain_core.tools import tool
from typing import List

# Simple TTL cache: key -> (result, expiry_ts)
_cache: dict = {}
_TTL = 300  # 5 minutes


@tool
async def retrieve_financial_insights(ticker: str, query: str) -> List[str]:
    """
    Searches embedded financial documents (annual reports, quarterly filings) in pgvector.

    Args:
        ticker: Stock ticker (e.g., "DANGCEM")
        query: What to search for (e.g., "revenue growth trends")

    Returns:
        List of chunks formatted as `[REF:n] 10-K FY2025, pg. 42: "Revenue grew 18.7%..."`
    """
    from src.adapters.storage.vector_store import PgVectorStore
    from src.adapters.embeddings.voyage_ai import VoyageAIEmbeddingAdapter
    from src.config.settings import settings

    cache_key = f"{ticker.upper()}::{query}"
    cached = _cache.get(cache_key)
    if cached and time.time() < cached[1]:
        return cached[0]

    store = PgVectorStore(database_url=settings.DATABASE_URL)
    embedder = VoyageAIEmbeddingAdapter(api_key=settings.VOYAGE_API_KEY)

    query_embedding = await embedder.embed_query(query)

    results = await store.search(
        query_embedding=query_embedding,
        top_k=5,
        filter_metadata={"ticker": ticker.upper()}
    )

    formatted_chunks = [
        f'[REF:{idx}] {res.metadata.get("doc_type", "10-K")} FY2025, pg. {res.metadata.get("page_number", "?")}: "{res.content}"'
        for idx, res in enumerate(results, start=1)
    ]

    _cache[cache_key] = (formatted_chunks, time.time() + _TTL)
    return formatted_chunks
