"""Embedding Service Port - Abstract interface for text embedding providers."""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    """Abstract base class for embedding providers (sentence-transformers, OpenAI, etc.)."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of embeddings produced by this service.

        Returns:
            Embedding dimension (e.g., 768 for multi-qa-mpnet-base-cos-v1)
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name/identifier of the embedding model.

        Returns:
            Model name string
        """
        pass
