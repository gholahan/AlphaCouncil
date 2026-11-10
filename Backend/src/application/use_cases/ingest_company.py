"""Ingest Company Document Use Case - Full PDF ingestion pipeline."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4
from pathlib import Path

from src.application.ports.outbound.pdf_downloader import PDFDownloaderPort
from src.application.ports.outbound.pdf_extractor import PDFExtractor
from src.domain.services.chunking import ChunkingService
from src.application.ports.outbound.embedding_service import EmbeddingService
from src.application.ports.outbound.vector_store import VectorStore
from src.application.ports.outbound.repository import CompanyRepository

logger = logging.getLogger(__name__)


class IngestCompanyDocumentUseCase:
    """
    Use case for ingesting company financial documents into the RAG system.

    Pipeline: PDF URL → Download → Extract Text → Chunk → Embed → Store in pgvector
    """

    def __init__(
        self,
        pdf_downloader: PDFDownloaderPort,
        pdf_extractor: PDFExtractor,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        company_repo: CompanyRepository,
    ):
        self.pdf_downloader = pdf_downloader
        self.pdf_extractor = pdf_extractor
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.company_repo = company_repo

    async def execute(
        self,
        ticker: str,
        pdf_url: str,
        filing_type: str,
        fiscal_year: int,
        quarter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute full PDF ingestion pipeline.

        Args:
            ticker: Company ticker (e.g., "DANGCEM")
            pdf_url: URL to download PDF from
            filing_type: "annual_report", "quarterly", or "news"
            fiscal_year: Fiscal year of the document
            quarter: "Q1", "Q2", "Q3", "Q4" (for quarterly reports)

        Returns:
            {
                "ticker": str,
                "filing_type": str,
                "chunks_stored": int,
                "embedding_dimensions": int,
                "pdf_name": str,
                "page_count": int,
                "processing_time_seconds": float,
            }
        """
        start_time = datetime.now(timezone.utc)
        ticker = ticker.upper()

        logger.info(f"Starting ingestion for {ticker} - {filing_type} FY{fiscal_year}")

        try:
            # Step 1: Download PDF
            logger.info(f"[1/6] Downloading PDF from {pdf_url}")
            pdf_path = await self.pdf_downloader.download_pdf(
                url=pdf_url,
                ticker=ticker,
                fiscal_year=fiscal_year,
            )
            pdf_name = Path(pdf_path).name

            # Step 2: Get PDF metadata
            logger.info(f"[2/6] Extracting PDF metadata")
            pdf_metadata = await self.pdf_extractor.get_metadata(pdf_path)
            page_count = pdf_metadata.get("page_count", 0)

            # Step 3: Extract text page by page
            logger.info(f"[3/6] Extracting text from {page_count} pages")
            pages = await self.pdf_extractor.extract_pages(pdf_path)

            # Combine all page text with page tracking
            full_text = ""
            page_boundaries = []  # [(page_num, char_start, char_end), ...]
            current_pos = 0

            for page in pages:
                page_text = page.text
                text_length = len(page_text)
                page_boundaries.append((page.page_number, current_pos, current_pos + text_length))
                full_text += page_text + "\n\n"
                current_pos += text_length + 2  # +2 for newlines

            # Step 4: Chunk text
            logger.info(f"[4/6] Chunking text into fixed-size overlapping chunks")
            chunks = self.chunking_service.chunk_financial_document(
                text=full_text,
                doc_type=filing_type,
                fiscal_year=fiscal_year,
                quarter=quarter,
            )

            # Add page numbers to chunks based on character positions
            for chunk in chunks:
                chunk_start = chunk["char_start"]
                chunk_end = chunk["char_end"]

                # Find which pages this chunk spans
                chunk_pages = []
                for page_num, page_start, page_end in page_boundaries:
                    # Check if chunk overlaps with this page
                    if chunk_start < page_end and chunk_end > page_start:
                        chunk_pages.append(page_num)

                # Add metadata
                chunk["metadata"]["page_number"] = chunk_pages[0] if chunk_pages else 1
                chunk["metadata"]["page_range"] = f"{min(chunk_pages)}-{max(chunk_pages)}" if len(chunk_pages) > 1 else str(chunk_pages[0]) if chunk_pages else "1"
                chunk["metadata"]["pdf_name"] = pdf_name
                chunk["metadata"]["ticker"] = ticker

            logger.info(f"Created {len(chunks)} chunks from {page_count} pages")

            # Step 5: Generate embeddings
            logger.info(f"[5/6] Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk["chunk_text"] for chunk in chunks]
            embeddings = await self.embedding_service.embed_batch(chunk_texts)
            embedding_dim = self.embedding_service.get_embedding_dimension()

            logger.info(f"Generated {len(embeddings)} embeddings ({embedding_dim} dimensions)")

            # Step 6: Store in pgvector
            logger.info(f"[6/6] Storing chunks in pgvector")
            chunks_stored = 0

            for chunk, embedding in zip(chunks, embeddings):
                doc_id = uuid4()
                await self.vector_store.upsert(
                    doc_id=doc_id,
                    text=chunk["chunk_text"],
                    embedding=embedding,
                    metadata={
                        "ticker": ticker,
                        "filing_type": filing_type,
                        "fiscal_year": fiscal_year,
                        "quarter": quarter,
                        "section": None,  # Not used with fixed-size chunking
                        "chunk_index": chunk["chunk_index"],
                        "page_number": chunk["metadata"]["page_number"],
                        "page_range": chunk["metadata"]["page_range"],
                        "pdf_name": pdf_name,
                        "char_start": chunk["char_start"],
                        "char_end": chunk["char_end"],
                    }
                )
                chunks_stored += 1

            # Update company last ingestion date
            await self.company_repo.update_last_ingested(ticker, datetime.now(timezone.utc))

            # Clean up downloaded PDF
            self.pdf_downloader.cleanup_file(pdf_path)

            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - start_time).total_seconds()

            logger.info(
                f"Ingestion complete: {ticker} - {chunks_stored} chunks stored "
                f"in {processing_time:.2f}s"
            )

            return {
                "ticker": ticker,
                "filing_type": filing_type,
                "fiscal_year": fiscal_year,
                "quarter": quarter,
                "chunks_stored": chunks_stored,
                "embedding_dimensions": embedding_dim,
                "pdf_name": pdf_name,
                "page_count": page_count,
                "processing_time_seconds": round(processing_time, 2),
            }

        except Exception as e:
            logger.error(f"Error during ingestion for {ticker}: {e}", exc_info=True)
            raise
