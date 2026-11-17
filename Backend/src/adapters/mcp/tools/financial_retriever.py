"""MCP Financial Retriever Tool - RAG search over financial documents with Voyage AI Reranker."""

import time
from langchain_core.tools import tool
from typing import List

# Simple TTL cache: key -> (result, expiry_ts)
_cache: dict = {}
_TTL = 300  # 5 minutes


@tool
async def retrieve_financial_insights(ticker: str, query: str) -> List[str]:
    """
    Searches embedded financial documents (annual reports, quarterly filings) in pgvector
    and reranks results using Voyage AI Reranker (rerank-2).

    Args:
        ticker: Stock ticker (e.g., "DANGCEM")
        query: What to search for (e.g., "revenue growth trends")

    Returns:
        List of reranked chunks formatted as `[REF:n] 10-K FY2025, pg. 42: "Revenue grew 18.7%..."`
    """
    from src.adapters.storage.vector_store import PgVectorStore
    from src.adapters.embeddings.voyage_embedding import VoyageAIEmbeddingAdapter
    from src.adapters.embeddings.voyage_reranker import VoyageRerankerAdapter
    from src.config.settings import settings

    cache_key = f"{ticker.upper()}::{query}"
    cached = _cache.get(cache_key)
    if cached and time.time() < cached[1]:
        return cached[0]

    store = PgVectorStore(database_url=settings.DATABASE_URL)
    embedder = VoyageAIEmbeddingAdapter(api_key=settings.VOYAGE_API_KEY)
    reranker = VoyageRerankerAdapter(api_key=settings.VOYAGE_API_KEY)

    # Step 1: Embed query and retrieve wider initial candidate pool from pgvector (top_k=20)
    query_embedding = await embedder.embed_query(query)

    candidates = await store.search(
        query_embedding=query_embedding,
        top_k=20,
        filter_metadata={"ticker": ticker.upper()}
    )

    if not candidates:
        return []

    # Step 2: Extract document texts for Voyage Reranker
    candidate_texts = [c.content for c in candidates]

    # Step 3: Rerank candidates using Voyage AI rerank-2 model (top_k=5)
    reranked_indices_scores = await reranker.rerank(
        query=query,
        documents=candidate_texts,
        top_k=5
    )

    # Step 4: Construct final formatted chunks ordered by rerank relevance score
    formatted_chunks = []
    for idx, (doc_idx, score) in enumerate(reranked_indices_scores, start=1):
        res = candidates[doc_idx]
        doc_type = res.metadata.get("doc_type", "10-K")
        fiscal_year = res.metadata.get("fiscal_year", "FY2025")
        page_num = res.metadata.get("page_number", "?")
        content = res.content
        formatted_chunks.append(
            f'[REF:{idx}] {doc_type} {fiscal_year}, pg. {page_num} (relevance: {score:.3f}): "{content}"'
        )

    _cache[cache_key] = (formatted_chunks, time.time() + _TTL)
    return formatted_chunks
