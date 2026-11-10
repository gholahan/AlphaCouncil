"""PDF Downloader Port - Abstract interface for downloading PDFs from URLs."""

from abc import ABC, abstractmethod
from typing import Optional


class PDFDownloaderPort(ABC):
    """Abstract port for PDF downloading operations."""

    @abstractmethod
    async def download_pdf(
        self,
        url: str,
        ticker: Optional[str] = None,
        fiscal_year: Optional[int] = None,
    ) -> str:
        """
        Download PDF from URL and return local file path.

        Args:
            url: PDF URL to download
            ticker: Optional ticker for filename
            fiscal_year: Optional year for filename

        Returns:
            str: Local file path to downloaded PDF

        Raises:
            ValueError: If URL is invalid or not a PDF
            Exception: If download fails
        """
        pass

    @abstractmethod
    def cleanup_file(self, file_path: str) -> None:
        """
        Clean up downloaded PDF file.

        Args:
            file_path: Path to file to delete
        """
        pass
