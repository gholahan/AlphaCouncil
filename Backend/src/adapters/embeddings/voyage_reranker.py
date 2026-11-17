"""Voyage AI Reranker Adapter - Implementation using rerank-3 model."""

import logging
from typing import List, Tuple, Optional
import voyageai

from src.application.ports.outbound.reranker import RerankerService
from src.config.settings import settings

logger = logging.getLogger(__name__)


class VoyageRerankerAdapter(RerankerService):
    """Adapter for Voyage AI Reranker using rerank-3 model."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.VOYAGE_API_KEY
        self.client = voyageai.Client(api_key=self.api_key)
        self.model = "rerank-3"

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        Rerank documents against a query using Voyage AI rerank-3 model.

        Args:
            query: Search query string
            documents: List of document text strings
            top_k: Number of top results to return

        Returns:
            List of tuples: (original_document_index, relevance_score) sorted by relevance descending.
        """
        if not documents:
            return []

        try:
            # Call Voyage AI rerank API
            result = self.client.rerank(
                query=query,
                documents=documents,
                model=self.model,
                top_k=min(top_k, len(documents))
            )

            # result.results contains list of objects with .index and .relevance_score
            ranked_results = [
                (res.index, float(res.relevance_score))
                for res in result.results
            ]
            return ranked_results
        except Exception as e:
            logger.error(f"Error calling Voyage AI reranker: {e}")
            # Fallback to original order if reranker fails
            return [(i, 1.0 - (i * 0.01)) for i in range(min(top_k, len(documents)))]
