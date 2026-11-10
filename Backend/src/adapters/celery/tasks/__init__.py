"""Celery tasks package."""

from src.adapters.celery.tasks.ingestion_tasks import ingest_pdf_document
from src.adapters.celery.tasks.debate_tasks import run_investment_debate

__all__ = ["ingest_pdf_document", "run_investment_debate"]
