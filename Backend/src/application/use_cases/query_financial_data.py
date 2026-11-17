"""Query Financial Data Use Case - RAG retrieval for financial insights with Reranker support."""

import logging
from typing import Dict, Any, List, Optional

from src.application.ports.outbound.embedding_service import EmbeddingService
from src.application.ports.outbound.vector_store import VectorStore
from src.application.ports.outbound.reranker import RerankerService

logger = logging.getLogger(__name__)


class QueryFinancialDataUseCase:
    """
    Use case for querying financial data using RAG (Retrieval-Augmented Generation) with Reranking.

    Pipeline: Query → Embed → Vector Search (Wide Pool) → Voyage Rerank → Return top-k relevant chunks
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        reranker_service: Optional[RerankerService] = None,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranker_service = reranker_service

    async def execute(
        self,
        ticker: str,
        query: str,
        top_k: int = 5,
        filing_type: Optional[str] = None,
        fiscal_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Query financial data for a company using RAG with optional Voyage AI Reranking.

        Args:
            ticker: Company ticker symbol (e.g., "DANGCEM")
            query: Natural language query (e.g., "What was the revenue in 2024?")
            top_k: Number of chunks to retrieve (default: 5)
            filing_type: Optional filter by document type ("annual_report", "quarterly", "news")
            fiscal_year: Optional filter by fiscal year
        """
        ticker = ticker.upper()

        logger.info(f"Querying financial data for {ticker}: {query}")

        try:
            # Step 1: Generate query embedding
            logger.info(f"[1/2] Generating query embedding")
            query_embedding = await self.embedding_service.embed_query(query)

            # Step 2: Vector similarity search (retrieve wider candidate pool if reranker is available)
            candidate_pool_size = max(20, top_k * 4) if self.reranker_service else top_k
            logger.info(f"[2/2] Searching vector store (top_k={candidate_pool_size})")
            results = await self.vector_store.query(
                embedding=query_embedding,
                ticker=ticker,
                top_k=candidate_pool_size,
                filing_type=filing_type,
                fiscal_year=fiscal_year,
            )

            if not results:
                return {
                    "ticker": ticker,
                    "query": query,
                    "chunks": [],
                    "total_chunks": 0,
                    "filters": {"filing_type": filing_type, "fiscal_year": fiscal_year}
                }

            # Step 3: Apply Voyage AI Reranker if available
            if self.reranker_service and len(results) > 0:
                document_texts = [r["chunk_text"] for r in results]
                reranked_pairs = await self.reranker_service.rerank(
                    query=query,
                    documents=document_texts,
                    top_k=top_k
                )

                reranked_results = []
                for doc_idx, score in reranked_pairs:
                    res = results[doc_idx]
                    res["score"] = score  # update with reranker relevance score
                    reranked_results.append(res)
                results = reranked_results
            else:
                results = results[:top_k]

            logger.info(f"Retrieved and reranked {len(results)} chunks for {ticker}")

            return {
                "ticker": ticker,
                "query": query,
                "chunks": results,
                "total_chunks": len(results),
                "filters": {
                    "filing_type": filing_type,
                    "fiscal_year": fiscal_year,
                }
            }

        except Exception as e:
            logger.error(f"Error querying financial data for {ticker}: {e}", exc_info=True)
            raise
