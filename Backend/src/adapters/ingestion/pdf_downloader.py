"""PDF Downloader Adapter - Download and validate PDFs from URLs."""

import logging
import httpx
import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from src.application.ports.outbound.pdf_downloader import PDFDownloaderPort

logger = logging.getLogger(__name__)


class PDFDownloader(PDFDownloaderPort):
    """Utility for downloading and validating PDF files from URLs."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = Path(temp_dir) if temp_dir else Path("/tmp/alphacouncil_pdfs")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = 60.0  # 60 seconds timeout

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
            httpx.HTTPError: If download fails
        """
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL scheme: {url}")

        # Generate filename
        if ticker and fiscal_year:
            filename = f"{ticker}_{fiscal_year}_{uuid4().hex[:8]}.pdf"
        else:
            filename = f"document_{uuid4().hex[:8]}.pdf"

        file_path = self.temp_dir / filename

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                logger.info(f"Downloading PDF from {url}")
                response = await client.get(url)
                response.raise_for_status()

                # Validate content type
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and not url.lower().endswith(".pdf"):
                    # Check PDF magic bytes (%PDF)
                    if not response.content[:4] == b"%PDF":
                        raise ValueError(f"URL does not point to a valid PDF: {url}")

                # Validate PDF magic bytes
                if response.content[:4] != b"%PDF":
                    raise ValueError(f"Downloaded file is not a valid PDF (missing %PDF header)")

                # Save to file
                with open(file_path, "wb") as f:
                    f.write(response.content)

                file_size_mb = len(response.content) / (1024 * 1024)
                logger.info(f"Downloaded PDF: {file_path} ({file_size_mb:.2f} MB)")

                return str(file_path)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading PDF from {url}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error downloading PDF from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF from {url}: {e}")
            if file_path.exists():
                file_path.unlink()  # Clean up partial download
            raise

    def cleanup_file(self, file_path: str) -> None:
        """Delete a downloaded PDF file."""
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.info(f"Cleaned up PDF file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clean up file {file_path}: {e}")

    def cleanup_old_files(self, days: int = 7) -> int:
        """
        Clean up PDF files older than specified days.

        Args:
            days: Delete files older than this many days

        Returns:
            Number of files deleted
        """
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in self.temp_dir.glob("*.pdf"):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Could not delete old file {file_path}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old PDF files")

        return deleted_count
