"""Celery tasks for PDF ingestion and vectorization."""

from typing import Dict, Any
from src.adapters.celery.app import celery_app
from src.adapters.celery.tasks.base import AsyncTask
from src.adapters.ingestion.pdf_downloader import PDFDownloader
from src.adapters.ingestion.pdf_extractor import PDFExtractorAdapter
from src.domain.services.chunking import ChunkingService
from src.adapters.embeddings.voyage_ai import VoyageAIEmbeddingAdapter
from src.adapters.storage.vector_store import PgVectorStore
from src.adapters.storage.repository import SQLModelCompanyRepository
from src.application.use_cases.ingest_company import IngestCompanyDocumentUseCase
from src.config.settings import settings


@celery_app.task(base=AsyncTask, bind=True, name="ingest_pdf_document")
async def ingest_pdf_document(
    self,
    ticker: str,
    pdf_url: str,
    filing_type: str,
    fiscal_year: int,
    quarter: str | None = None,
) -> Dict[str, Any]:
    """
    Background task: Ingest PDF document into vector store.

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
    pdf_downloader = PDFDownloader()
    pdf_extractor = PDFExtractorAdapter()
    chunking_service = ChunkingService(chunk_size=2000, chunk_overlap=200)
    embedding_service = VoyageAIEmbeddingAdapter(api_key=settings.VOYAGE_API_KEY)
    vector_store = PgVectorStore(database_url=settings.DATABASE_URL)
    company_repo = SQLModelCompanyRepository(database_url=settings.DATABASE_URL)

    use_case = IngestCompanyDocumentUseCase(
        pdf_downloader=pdf_downloader,
        pdf_extractor=pdf_extractor,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        vector_store=vector_store,
        company_repo=company_repo,
    )

    result = await use_case.execute(
        ticker=ticker,
        pdf_url=pdf_url,
        filing_type=filing_type,
        fiscal_year=fiscal_year,
        quarter=quarter,
    )

    return result
