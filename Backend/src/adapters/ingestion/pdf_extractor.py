"""PDF Extractor Adapter - Implementation of PDFExtractor port using pdfplumber."""

import logging
import pdfplumber
from typing import List, Dict, Any, Optional

from src.application.ports.outbound.pdf_extractor import PDFExtractor, PDFPage

logger = logging.getLogger(__name__)


class PDFExtractorAdapter(PDFExtractor):
    """Adapter for extracting text, tables, and metadata from PDF documents using pdfplumber."""

    async def extract_text(
        self,
        pdf_path: str,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> str:
        """
        Extract plain text from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            start_page: Optional starting page number (1-indexed)
            end_page: Optional ending page number (1-indexed)

        Returns:
            Extracted text as a single string
        """
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                # Convert 1-indexed to 0-indexed slicing
                start_idx = (start_page - 1) if start_page is not None else 0
                end_idx = end_page if end_page is not None else total_pages

                start_idx = max(0, min(start_idx, total_pages))
                end_idx = max(start_idx, min(end_idx, total_pages))

                for i in range(start_idx, end_idx):
                    page = pdf.pages[i]
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted)

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise

    async def extract_pages(
        self,
        pdf_path: str,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> List[PDFPage]:
        """
        Extract text page by page from a PDF.

        Args:
            pdf_path: Path to the PDF file
            start_page: Optional starting page number (1-indexed)
            end_page: Optional ending page number (1-indexed)

        Returns:
            List of PDFPage objects with per-page content
        """
        try:
            pages_list = []
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                start_idx = (start_page - 1) if start_page is not None else 0
                end_idx = end_page if end_page is not None else total_pages

                start_idx = max(0, min(start_idx, total_pages))
                end_idx = max(start_idx, min(end_idx, total_pages))

                for i in range(start_idx, end_idx):
                    page_num = i + 1
                    page = pdf.pages[i]
                    text = page.extract_text() or ""

                    # Extract tables for this page if any
                    tables = page.extract_tables() or []

                    pages_list.append(
                        PDFPage(
                            page_number=page_num,
                            text=text,
                            tables=tables,
                            metadata={"width": page.width, "height": page.height}
                        )
                    )

            return pages_list
        except Exception as e:
            logger.error(f"Error extracting pages from PDF {pdf_path}: {e}")
            raise

    async def extract_tables(self, pdf_path: str, page_number: int) -> List[List[List[str]]]:
        """
        Extract tables from a specific PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to extract tables from (1-indexed)

        Returns:
            List of tables, where each table is a list of rows, each row is a list of cells
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if page_number < 1 or page_number > total_pages:
                    raise ValueError(f"Page number {page_number} out of range (1-{total_pages})")

                page = pdf.pages[page_number - 1]
                tables = page.extract_tables()
                return tables or []
        except Exception as e:
            logger.error(f"Error extracting tables from PDF {pdf_path} page {page_number}: {e}")
            raise

    async def get_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get PDF metadata (author, title, page count, etc.).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict with metadata fields
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                meta = pdf.metadata or {}
                meta["page_count"] = len(pdf.pages)
                return meta
        except Exception as e:
            logger.error(f"Error getting metadata for PDF {pdf_path}: {e}")
            raise

    async def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Total page count
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.error(f"Error getting page count for PDF {pdf_path}: {e}")
            raise
