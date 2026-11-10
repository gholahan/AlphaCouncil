"""Celery tasks for running multi-agent investment debates."""

from typing import Dict, Any
from src.adapters.celery.app import celery_app
from src.adapters.celery.tasks.base import AsyncTask
from src.adapters.embeddings.voyage_ai import VoyageAIEmbeddingAdapter
from src.adapters.storage.vector_store import PgVectorStore
from src.adapters.storage.repository import SQLModelCompanyRepository, SQLModelDebateRepository, SQLModelDebateTurnRepository
from src.application.use_cases.query_financial_data import QueryFinancialDataUseCase
from src.application.use_cases.run_investment_debate import RunInvestmentDebateUseCase
from src.adapters.orchestration.langgraph_engine import LangGraphMADEngine
from src.config.settings import settings


@celery_app.task(base=AsyncTask, bind=True, name="run_investment_debate")
async def run_investment_debate(
    self,
    ticker: str,
    user_thesis: str | None = None,
    capital_to_deploy: float = 1000000.0,
    risk_tolerance: str = "moderate",
    current_price: float | None = None,
    max_rounds: int = 3,
) -> Dict[str, Any]:
    """
    Background task: Run MAD (Multi Agent Debate) investment analysis.
    """
    embedding_service = VoyageAIEmbeddingAdapter(api_key=settings.VOYAGE_API_KEY)
    vector_store = PgVectorStore(database_url=settings.DATABASE_URL)
    company_repo = SQLModelCompanyRepository(database_url=settings.DATABASE_URL)
    debate_repo = SQLModelDebateRepository(database_url=settings.DATABASE_URL)
    turn_repo = SQLModelDebateTurnRepository(database_url=settings.DATABASE_URL)

    mad_engine = LangGraphMADEngine(
        model_name=settings.DEFAULT_OPENROUTER_MODEL if settings.DEFAULT_LLM_PROVIDER == "openrouter" else settings.DEFAULT_GROQ_MODEL,
        llm_provider=settings.DEFAULT_LLM_PROVIDER,
    )

    query_financial_data = QueryFinancialDataUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    use_case = RunInvestmentDebateUseCase(
        mad_engine=mad_engine,
        debate_repo=debate_repo,
        turn_repo=turn_repo,
        company_repo=company_repo,
        query_financial_data=query_financial_data,
    )

    result = await use_case.execute(
        ticker=ticker,
        user_thesis=user_thesis,
        capital_to_deploy=capital_to_deploy,
        risk_tolerance=risk_tolerance,
        current_price=current_price,
        max_rounds=max_rounds,
    )

    return result
