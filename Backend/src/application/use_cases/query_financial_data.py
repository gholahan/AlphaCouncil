"""Query Financial Data Use Case - RAG retrieval for financial insights."""

import logging
from typing import Dict, Any, List, Optional

from src.application.ports.outbound.embedding_service import EmbeddingService
from src.application.ports.outbound.vector_store import VectorStore

logger = logging.getLogger(__name__)


class QueryFinancialDataUseCase:
    """
    Use case for querying financial data using RAG (Retrieval-Augmented Generation).

    Pipeline: Query → Embed → Vector Search → Return relevant chunks
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def execute(
        self,
        ticker: str,
        query: str,
        top_k: int = 5,
        filing_type: Optional[str] = None,
        fiscal_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Query financial data for a company using RAG.

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

            # Step 2: Vector similarity search
            logger.info(f"[2/2] Searching vector store (top_k={top_k})")
            results = await self.vector_store.query(
                embedding=query_embedding,
                ticker=ticker,
                top_k=top_k,
                filing_type=filing_type,
                fiscal_year=fiscal_year,
            )

            logger.info(f"Retrieved {len(results)} chunks for {ticker}")

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
