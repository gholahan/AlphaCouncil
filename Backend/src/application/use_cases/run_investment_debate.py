"""Run Investment Debate Use Case - Orchestrate the full MAD debate workflow."""

import re
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.adapters.orchestration.langgraph_engine import LangGraphMADEngine
from src.application.ports.outbound.repository import DebateRepository, CompanyRepository, DebateTurnRepository
from src.application.use_cases.query_financial_data import QueryFinancialDataUseCase

logger = logging.getLogger(__name__)

_CITATION_RE = re.compile(r'\[(?:REF|WEB):\d+\]')


def _extract_citations(content: str) -> List[str]:
    return list(dict.fromkeys(_CITATION_RE.findall(content)))  # unique, order-preserved


class RunInvestmentDebateUseCase:

    def __init__(
        self,
        mad_engine: LangGraphMADEngine,
        debate_repo: DebateRepository,
        company_repo: CompanyRepository,
        query_financial_data: QueryFinancialDataUseCase,
        turn_repo: Optional[DebateTurnRepository] = None,
    ):
        self.mad_engine = mad_engine
        self.debate_repo = debate_repo
        self.turn_repo = turn_repo
        self.company_repo = company_repo
        self.query_financial_data = query_financial_data

    async def execute(
        self,
        ticker: str,
        user_thesis: Optional[str] = None,
        capital_to_deploy: float = 1000000.0,
        risk_tolerance: str = "moderate",
        current_price: Optional[float] = None,
        max_rounds: int = 3,
    ) -> Dict[str, Any]:
        ticker = ticker.upper()
        start_time = datetime.utcnow()

        logger.info(f"Starting MAD debate for {ticker} - Capital: {capital_to_deploy:,.0f} NGN")

        try:
            # Step 0: Fetch live market price from KoboTerminal if not provided
            price_timestamp = None
            if current_price is None or current_price <= 0:
                try:
                    from src.adapters.market_data.kobo_terminal import KoboTerminalAdapter
                    adapter = KoboTerminalAdapter()
                    quote = await adapter.get_quote(ticker)
                    await adapter.close()
                    if quote and quote.price > 0:
                        current_price = quote.price
                        price_timestamp = quote.timestamp
                        logger.info(f"Fetched live price for {ticker} from KoboTerminal: ₦{current_price} (timestamp: {price_timestamp})")
                except Exception as e:
                    logger.warning(f"Failed to fetch live price from KoboTerminal for {ticker}: {e}")

            # Step 1: Create debate record
            debate_id = await self.debate_repo.create({
                "ticker": ticker,
                "user_thesis": user_thesis,
                "capital_to_deploy": capital_to_deploy,
                "risk_tolerance": risk_tolerance,
            })
            logger.info(f"Created debate record: {debate_id}")

            # Step 2: Company metadata
            company = await self.company_repo.get_by_ticker(ticker)
            company_name = company.get("name", ticker) if company else ticker
            if not company:
                logger.warning(f"Company {ticker} not found in database")

            # Step 3: RAG retrieval
            logger.info(f"[1/3] Querying financial data for {ticker}")
            context_query = (
                f"Given the thesis: {user_thesis}, provide relevant financial data and analysis"
                if user_thesis else
                "Provide comprehensive financial overview including revenue, profit margins, "
                "balance sheet health, cash flow, competitive position, and growth prospects"
            )
            financial_context = await self.query_financial_data.execute(
                ticker=ticker, query=context_query, top_k=10,
            )
            financial_chunks = [
                {
                    "content": chunk["chunk_text"],
                    "source": chunk["metadata"].get("pdf_name", "Unknown"),
                    "page": chunk["metadata"].get("page_number", 0),
                }
                for chunk in financial_context["chunks"]
            ]
            logger.info(f"Retrieved {len(financial_chunks)} financial chunks")

            # Step 4: Run MAD debate
            logger.info(f"[2/3] Running MAD debate (max {max_rounds} rounds)")
            debate_result = await self.mad_engine.run_debate(
                ticker=ticker,
                company_name=company_name,
                user_thesis=user_thesis,
                financial_context=financial_chunks,
                capital=capital_to_deploy,
                risk_tolerance=risk_tolerance,
                current_price=current_price,
                max_rounds=max_rounds,
            )

            # Step 5: Extract verdict and recommendation
            verdict = debate_result.get("verdict", "HOLD")
            recommendation = debate_result.get("recommendation") or {}
            transcript = debate_result.get("messages", [])
            chat_response = debate_result.get("chat_response")

            bull_outputs = [
                msg.content for msg in transcript
                if hasattr(msg, "name") and msg.name and "bull" in msg.name
            ]
            bear_outputs = [
                msg.content for msg in transcript
                if hasattr(msg, "name") and msg.name and "bear" in msg.name
            ]
            arbitrator_outputs = [
                msg.content for msg in transcript
                if hasattr(msg, "name") and msg.name and "arbitrator" in msg.name
            ]

            # Serialize transcript for debate_traces.transcript (JSON column)
            serialized_transcript = [
                {
                    "turn": idx + 1,
                    "role": getattr(msg, "name", None) or getattr(msg, "type", "unknown"),
                    "content": getattr(msg, "content", ""),
                }
                for idx, msg in enumerate(transcript)
            ]

            # Build debate_turns rows (one per agent message)
            turn_rows = [
                {
                    "turn_number": idx + 1,
                    "agent_role": getattr(msg, "name", None) or getattr(msg, "type", "unknown"),
                    "content": getattr(msg, "content", ""),
                    "citations": _extract_citations(getattr(msg, "content", "")),
                    "tools_called": [
                        {"name": tc["name"], "args": tc["args"]}
                        for tc in (getattr(msg, "tool_calls", None) or [])
                    ] or None,
                    "token_count": None,  # OpenRouter doesn't return per-message token counts
                }
                for idx, msg in enumerate(transcript)
            ]

            # Step 6: Write debate_traces + debate_turns concurrently
            logger.info(f"[3/3] Saving verdict: {verdict}")

            save_trace = self.debate_repo.save_verdict(
                debate_id=debate_id,
                verdict={
                    "verdict": verdict,
                    "recommendation": recommendation,
                    "transcript": serialized_transcript,
                    "chat_response": chat_response,
                },
            )
            save_turns = (
                self.turn_repo.create_many(debate_id=debate_id, turns=turn_rows)
                if self.turn_repo else asyncio.sleep(0)
            )
            await asyncio.gather(save_trace, save_turns)

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            logger.info(
                f"MAD debate complete for {ticker}: {verdict} - "
                f"{processing_time:.2f}s - Transcript: {len(transcript)} turns"
            )

            return {
                "debate_id": debate_id,
                "ticker": ticker,
                "company_name": company_name,
                "verdict": verdict,
                "recommendation": recommendation,
                "chat_response": chat_response,
                "transcript": serialized_transcript,
                "bull_case_summary": "\n\n".join(bull_outputs) or "No bull case presented",
                "bear_case_summary": "\n\n".join(bear_outputs) or "No bear case presented",
                "arbitrator_reasoning": "\n\n".join(arbitrator_outputs) or "No final verdict",
                "financial_context_chunks": len(financial_chunks),
                "debate_rounds": len(bull_outputs),
                "processing_time_seconds": round(processing_time, 2),
                "created_at": start_time,
            }

        except Exception as e:
            logger.error(f"Error during MAD debate for {ticker}: {e}", exc_info=True)
            raise
