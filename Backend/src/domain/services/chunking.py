"""Chunking Service - Fixed-size overlapping chunking using LangChain RecursiveCharacterTextSplitter."""

from typing import List, Dict, Any, Optional
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for fixed-size overlapping chunking of financial documents using LangChain."""

    def __init__(
        self,
        chunk_size: int = 2000,  # Characters, not tokens
        chunk_overlap: int = 200,
    ):
        """
        Initialize chunking service with LangChain RecursiveCharacterTextSplitter.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap size in characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize LangChain splitter
        # Uses hierarchical separators: \n\n, \n, space, then character-level
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_financial_document(
        self,
        text: str,
        doc_type: str,
        fiscal_year: Optional[int] = None,
        quarter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk financial document with fixed-size overlapping chunks using LangChain.

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for chunking")
            return []

        # Clean text
        text = self._clean_text(text)

        # Split using LangChain
        chunks = self.text_splitter.create_documents([text])

        # Format chunks with metadata
        formatted_chunks = []
        current_pos = 0

        for idx, chunk in enumerate(chunks):
            chunk_text = chunk.page_content
            chunk_length = len(chunk_text)

            # Find position in original text (approximate)
            chunk_start = text.find(chunk_text, current_pos)
            if chunk_start == -1:
                chunk_start = current_pos
            chunk_end = chunk_start + chunk_length
            current_pos = chunk_start + (chunk_length - self.chunk_overlap)

            formatted_chunks.append({
                "chunk_text": chunk_text,
                "chunk_index": idx,
                "char_start": chunk_start,
                "char_end": chunk_end,
                "token_estimate": self._estimate_tokens(chunk_text),
                "metadata": {
                    "doc_type": doc_type,
                    "fiscal_year": fiscal_year,
                    "quarter": quarter,
                }
            })

        logger.info(
            f"Chunked document into {len(formatted_chunks)} chunks "
            f"(chunk_size={self.chunk_size} chars, overlap={self.chunk_overlap} chars)"
        )
        return formatted_chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize document text."""
        import re

        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double newline

        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

        return text.strip()

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (1 token ≈ 4 characters for English).

        This is a rough approximation. Actual tokenization varies by model.
        """
        return len(text) // 4
