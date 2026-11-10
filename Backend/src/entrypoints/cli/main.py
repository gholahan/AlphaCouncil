"""CLI entry point with logging initialization."""

import sys
import click
import asyncio
from pathlib import Path

# IMPORTANT: Initialize logging BEFORE any other imports
from config.logging import setup_logging_from_settings, get_logger

# Setup logging first
setup_logging_from_settings()
logger = get_logger(__name__)

# Now import everything else
from config.settings import get_settings

settings = get_settings()


@click.group()
@click.version_option(version=settings.APP_VERSION)
def cli():
    """AlphaCouncil CLI - Multi-agent investment analysis platform."""
    logger.info(f"Starting {settings.APP_NAME} CLI v{settings.APP_VERSION}")


@cli.command()
@click.argument("ticker", type=str)
@click.option("--pdf", type=click.Path(exists=True), help="Path to financial document PDF")
@click.option("--year", type=int, help="Fiscal year")
def ingest(ticker: str, pdf: str = None, year: int = None):
    """
    Ingest company financial data.

    Example:
        python -m entrypoints.cli.main ingest AAPL --pdf annual_report.pdf --year 2023
    """
    logger.info(f"Ingesting data for {ticker}")

    try:
        from entrypoints.cli.ingest import ingest_company

        asyncio.run(ingest_company(
            ticker=ticker,
            pdf_path=pdf,
            year=year
        ))

        logger.info(f"Successfully ingested {ticker}")
        click.echo(f"✓ Company {ticker} ingested successfully")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("ticker", type=str)
@click.option("--rounds", type=int, default=3, help="Number of debate rounds")
@click.option("--model", type=str, help="LLM model to use")
def debate(ticker: str, rounds: int = 3, model: str = None):
    """
    Run investment debate for a company.

    Example:
        python -m entrypoints.cli.main debate AAPL --rounds 3
    """
    logger.info(f"Starting debate for {ticker} with {rounds} rounds")

    try:
        from application.use_cases.run_investment_debate import run_investment_debate

        result = asyncio.run(run_investment_debate(
            ticker=ticker,
            max_rounds=rounds,
            model=model or settings.DEFAULT_GROQ_MODEL
        ))

        logger.info(f"Debate completed for {ticker}")

        click.echo(f"\n{'='*60}")
        click.echo(f"Debate Result for {ticker}")
        click.echo(f"{'='*60}")
        click.echo(f"Decision: {result.get('decision', 'N/A')}")
        click.echo(f"Confidence: {result.get('confidence', 'N/A')}")
        click.echo(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"Debate failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("ticker", type=str)
def query(ticker: str):
    """
    Query financial data for a company.

    Example:
        python -m entrypoints.cli.main query AAPL
    """
    logger.info(f"Querying data for {ticker}")

    try:
        from application.use_cases.query_financial_data import query_financial_data

        data = asyncio.run(query_financial_data(ticker=ticker))

        click.echo(f"\n{'='*60}")
        click.echo(f"Financial Data for {ticker}")
        click.echo(f"{'='*60}")
        click.echo(data)
        click.echo(f"{'='*60}\n")

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def migrate():
    """
    Run database migrations.

    Example:
        python -m entrypoints.cli.main migrate
    """
    logger.info("Running database migrations")

    try:
        from entrypoints.cli.migrate import run_migrations

        asyncio.run(run_migrations())

        logger.info("Migrations completed successfully")
        click.echo("✓ Database migrations completed")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def preload():
    """
    Preload data and warm up caches.

    Example:
        python -m entrypoints.cli.main preload
    """
    logger.info("Preloading data")

    try:
        from entrypoints.cli.preload import preload_data

        asyncio.run(preload_data())

        logger.info("Preload completed successfully")
        click.echo("✓ Data preloaded successfully")

    except Exception as e:
        logger.error(f"Preload failed: {e}", exc_info=True)
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def config():
    """Display current configuration."""
    click.echo(f"\n{'='*60}")
    click.echo(f"{settings.APP_NAME} Configuration")
    click.echo(f"{'='*60}")
    click.echo(f"Version: {settings.APP_VERSION}")
    click.echo(f"Environment: {settings.ENVIRONMENT}")
    click.echo(f"Debug: {settings.DEBUG}")
    click.echo(f"Log Level: {settings.LOG_LEVEL}")
    click.echo(f"Database: {settings.DATABASE_URL}")
    click.echo(f"Default LLM: {settings.DEFAULT_LLM_PROVIDER}")
    click.echo(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logger.info("CLI interrupted by user")
        click.echo("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        click.echo(f"\n✗ Fatal error: {e}", err=True)
        sys.exit(1)
