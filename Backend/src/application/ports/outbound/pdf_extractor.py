"""PDF Extractor Port - Abstract interface for PDF text extraction."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PDFPage:
    """Extracted content from a single PDF page."""

    page_number: int
    text: str
    tables: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class PDFExtractor(ABC):
    """Abstract base class for PDF extraction libraries (pdfplumber, PyMuPDF, etc.)."""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def extract_tables(self, pdf_path: str, page_number: int) -> List[List[List[str]]]:
        """
        Extract tables from a specific PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to extract tables from (1-indexed)

        Returns:
            List of tables, where each table is a list of rows, each row is a list of cells
        """
        pass

    @abstractmethod
    async def get_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get PDF metadata (author, title, page count, etc.).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict with metadata fields
        """
        pass

    @abstractmethod
    async def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Total page count
        """
        pass
