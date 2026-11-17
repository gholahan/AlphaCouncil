"""Outbound port for document reranking services."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class RerankerService(ABC):
    """Abstract port for reranking retrieved documents against a query."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        Rerank a list of document strings against a query.

        Args:
            query: Search query string
            documents: List of document text strings
            top_k: Number of top results to return

        Returns:
            List of tuples: (original_document_index, relevance_score)
        """
        pass
