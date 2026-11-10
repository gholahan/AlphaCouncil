"""Vector Store Port - Abstract interface for vector similarity search."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search."""
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    distance: float


class VectorStore(ABC):
    """Abstract base class for vector databases (pgvector, Pinecone, etc.)."""

    @abstractmethod
    async def insert(
        self,
        id: str,
        embedding: List[float],
        content: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Insert a single vector with metadata.

        Args:
            id: Unique identifier for the vector
            embedding: Vector representation
            content: Original text content
            metadata: Additional metadata (ticker, page_number, doc_type, etc.)
        """
        pass

    @abstractmethod
    async def insert_batch(
        self,
        records: List[Dict[str, Any]],
    ) -> None:
        """
        Insert multiple vectors in batch.

        Args:
            records: List of dicts with 'id', 'embedding', 'content', 'metadata'
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """
        Search for similar vectors using cosine similarity.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {'ticker': 'DANGCEM'})

        Returns:
            List of search results ordered by similarity (highest first)
        """
        pass

    @abstractmethod
    async def delete_by_id(self, id: str) -> None:
        """
        Delete a vector by ID.

        Args:
            id: Vector identifier to delete
        """
        pass

    @abstractmethod
    async def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> int:
        """
        Delete vectors matching metadata filters.

        Args:
            filter_metadata: Metadata filters (e.g., {'ticker': 'DANGCEM'})

        Returns:
            Number of vectors deleted
        """
        pass

    @abstractmethod
    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Count vectors, optionally filtered by metadata.

        Args:
            filter_metadata: Optional metadata filters

        Returns:
            Count of matching vectors
        """
        pass
