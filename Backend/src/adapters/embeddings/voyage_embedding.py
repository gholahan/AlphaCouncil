"""Voyage AI Embedding Adapter - Implementation using voyage-finance-2 model."""

import logging
from typing import List, Optional
import voyageai

from src.application.ports.outbound.embedding_service import EmbeddingService
from src.config.settings import settings

logger = logging.getLogger(__name__)


class VoyageAIEmbeddingAdapter(EmbeddingService):
    """Adapter for Voyage AI embeddings using voyage-finance-2 model (1024 dimensions)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.VOYAGE_API_KEY
        self.client = voyageai.Client(api_key=self.api_key)
        self.model = "voyage-finance-2"
        self.embedding_dim = 1024

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            1024-dimensional embedding vector
        """
        try:
            result = self.client.embed(
                texts=[text],
                model=self.model,
                input_type="document"
            )
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"Error generating Voyage AI embedding: {e}")
            raise

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 128
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per API call (Voyage AI limit: 128)

        Returns:
            List of 1024-dimensional embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []

        try:
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Embedding batch {i // batch_size + 1}: {len(batch)} texts")

                result = self.client.embed(
                    texts=batch,
                    model=self.model,
                    input_type="document"
                )
                all_embeddings.extend(result.embeddings)

            return all_embeddings
        except Exception as e:
            logger.error(f"Error batch embedding with Voyage AI: {e}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            1024-dimensional query embedding
        """
        try:
            result = self.client.embed(
                texts=[query],
                model=self.model,
                input_type="query"
            )
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Return the embedding dimension for this model."""
        return self.embedding_dim

    def get_model_name(self) -> str:
        """Return the model name."""
        return self.model
