"""LangGraph Debate Engine - Supervisor-controlled MAD with dynamic analyst node."""

import logging
import json
import re
from typing import Dict, Any, Optional, Literal, List
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END

from src.adapters.orchestration.debate_state import DebateState
from src.adapters.orchestration.personas import AgentRole
from src.adapters.orchestration.prompt_reader import build_agent_prompt
from src.adapters.orchestration.tool_registry import get_tools_for_role_objects, TOOL_MAP
from src.adapters.orchestration.arbitrator_schemas import (
    ArbitratorResponse,
    calculate_recommendation,
)
from src.application.ports.outbound.llm_client import LLMClient
from src.adapters.llm.groq_client import GroqClientAdapter
from src.adapters.llm.openrouter_client import OpenRouterClientAdapter

logger = logging.getLogger(__name__)


class LangGraphDebateEngine:
    """
    Supervisor-controlled MAD (Multi Agent Debate) architecture.

    Graph: Supervisor → Analyst (dynamic Bull/Bear) → Supervisor → Arbitrator → END
    """

    def __init__(
        self,
        model_name: str = "llama3-70b-8192",
        temperature: float = 0.7,
        llm_client: Optional[LLMClient] = None,
        llm_provider: str = "openrouter",
        max_rounds: int = 3,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_rounds = max_rounds
        if llm_client:
            self.llm_client = llm_client
        elif llm_provider == "openrouter":
            self.llm_client = OpenRouterClientAdapter(default_model=model_name)
        else:
            self.llm_client = GroqClientAdapter(default_model=model_name)
        self.llm = self.llm_client.get_chat_model(model=self.model_name, temperature=self.temperature)
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build workflow: Supervisor routes to dynamic Analyst or Arbitrator."""
        workflow = StateGraph(DebateState)

        workflow.add_node("supervisor", self._supervisor)
        workflow.add_node("analyst", self._analyst)
        workflow.add_node("arbitrator", self._arbitrator)

        workflow.set_entry_point("supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            self._route_supervisor,
            {
                "analyst": "analyst",
                "arbitrator": "arbitrator",
                "end": END,
            }
        )

        workflow.add_edge("analyst", "supervisor")
        workflow.add_edge("arbitrator", END)

        return workflow.compile()

    def _route_supervisor(self, state: DebateState) -> Literal["analyst", "arbitrator", "end"]:
        """Route based on supervisor's next_agent decision."""
        next_agent = state.get("next_agent")

        if next_agent in ["bull_analyst", "bear_analyst"]:
            return "analyst"
        elif next_agent == "arbitrator":
            return "arbitrator"
        else:
            return "end"

    async def _supervisor(self, state: DebateState) -> Dict[str, Any]:
        """Supervisor: orchestrate rounds and decide when to escalate to CIO."""
        round_count = state.get("round_count", 0)
        max_rounds = state.get("max_rounds", self.max_rounds)
        bull_outputs = state.get("bull_case_outputs", [])
        bear_outputs = state.get("bear_case_outputs", [])
        ticker = state.get("ticker", "")

        logger.info(f"[Supervisor] Round {round_count}/{max_rounds} | Bull: {len(bull_outputs)} | Bear: {len(bear_outputs)}")

        if round_count == 0:
            logger.info("[Supervisor] → Bull Analyst")
            return {"next_agent": "bull_analyst", "round_count": 1, "max_rounds": max_rounds}

        if len(bull_outputs) > len(bear_outputs):
            logger.info("[Supervisor] → Bear Analyst")
            return {"next_agent": "bear_analyst"}

        if len(bull_outputs) > 0 and len(bear_outputs) > 0 and len(bull_outputs) == len(bear_outputs):
            if round_count >= max_rounds:
                logger.info(f"[Supervisor] Max rounds reached → CIO Arbitrator")
                return {"next_agent": "arbitrator"}

            supervisor_prompt = build_agent_prompt(
                role=AgentRole.SUPERVISOR,
                ticker=ticker,
                round_count=round_count,
                max_rounds=max_rounds,
                bull_outputs_count=len(bull_outputs),
                bear_outputs_count=len(bear_outputs),
                bull_case_latest=bull_outputs,
                bear_case_latest=bear_outputs,
            )

            supervisor_llm = self.llm_client.get_chat_model(model=self.model_name, temperature=0.3)
            messages = [SystemMessage(content=supervisor_prompt), HumanMessage(content="Evaluate debate convergence and decide next step.")]
            response = await supervisor_llm.ainvoke(messages)
            output_content = response.content or ""

            decision = "CONTINUE"
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', output_content)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    next_agent_decision = data.get("next_agent", "").strip().lower()
                    if next_agent_decision in ["arbitrator", "cio", "end"]:
                        decision = "CONVERGED"
                except Exception:
                    pass

            if "CONVERGED" in output_content.upper() or decision == "CONVERGED":
                logger.info(f"[Supervisor] Converged → CIO Arbitrator")
                return {"next_agent": "arbitrator"}
            else:
                logger.info(f"[Supervisor] Continue → Bull Analyst (Round {round_count + 1})")
                return {"next_agent": "bull_analyst", "round_count": round_count + 1}

        logger.info("[Supervisor] Unexpected state → End")
        return {"next_agent": "end"}

    async def _analyst(self, state: DebateState) -> Dict[str, Any]:
        """Dynamic analyst: switches between Bull/Bear based on state.next_agent."""
        next_agent = state.get("next_agent")
        round_count = state.get("round_count", 1)

        if next_agent == "bull_analyst":
            return await self._run_analyst_role(
                state,
                role=AgentRole.BULL_ANALYST,
                round_count=round_count,
                output_key="bull_case_outputs",
                role_name="Bull Analyst"
            )
        elif next_agent == "bear_analyst":
            return await self._run_analyst_role(
                state,
                role=AgentRole.BEAR_ANALYST,
                round_count=round_count,
                output_key="bear_case_outputs",
                role_name="Bear Analyst"
            )
        else:
            logger.error(f"[Analyst] Unexpected next_agent: {next_agent}")
            return {}

    async def _run_analyst_role(
        self,
        state: DebateState,
        role: AgentRole,
        round_count: int,
        output_key: str,
        role_name: str,
    ) -> Dict[str, Any]:
        """Execute analyst role with dynamic prompt and tool binding."""
        logger.info(f"[{role_name}] Round {round_count}")
        ticker = state.get("ticker", "")
        company_name = state.get("company_name", ticker)
        financial_context = state.get("financial_context", [])

        if role == AgentRole.BULL_ANALYST:
            system_prompt = build_agent_prompt(
                role=role,
                ticker=ticker,
                company_name=company_name,
                user_thesis=state.get("user_thesis"),
                financial_context=financial_context,
            )
            bear_outputs = state.get("bear_case_outputs", [])
            if round_count == 1:
                user_message = f"Build the bull case for {company_name} ({ticker})."
            else:
                latest_bear = bear_outputs[-1] if bear_outputs else ""
                user_message = f"Bear challenged your case. Strengthen with new evidence for {company_name} ({ticker}).\n\nBear's challenge (R{round_count - 1}):\n{latest_bear[-500:]}"
        else:
            bull_outputs = state.get("bull_case_outputs", [])
            latest_bull = bull_outputs[-1] if bull_outputs else ""
            system_prompt = build_agent_prompt(
                role=role,
                ticker=ticker,
                company_name=company_name,
                bull_case_output=latest_bull,
                financial_context=financial_context,
            )
            user_message = f"Stress-test the bull case for {company_name} ({ticker}). Find hidden risks and challenge key claims."

        tools = get_tools_for_role_objects(role.value)
        llm_with_tools = self.llm.bind_tools(tools)

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        response = await llm_with_tools.ainvoke(messages)
        output_content = response.content or ""

        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)
            for tc in response.tool_calls:
                tool_fn = TOOL_MAP.get(tc["name"])
                if tool_fn:
                    logger.info(f"[{role_name}] Tool called: {tc['name']} with args {tc['args']}")
                    try:
                        tool_result = await tool_fn.ainvoke(tc["args"])
                    except Exception as e:
                        logger.error(f"[{role_name}] Tool {tc['name']} error: {e}")
                        tool_result = {"error": str(e)}
                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))

            final_response = await llm_with_tools.ainvoke(messages)
            output_content = final_response.content or output_content

        # If still empty, ask for a plain text synthesis (no tools)
        if not output_content.strip():
            fallback = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"{user_message}\n\nProvide your analysis in plain text now.")
            ])
            output_content = fallback.content or f"[{role_name}] No output generated."

        return {
            output_key: [output_content],
            "messages": [AIMessage(content=output_content, name=f"{role.value}_round_{round_count}")]
        }

    async def _arbitrator(self, state: DebateState) -> Dict[str, Any]:
        """CIO Arbitrator: receives full debate history and delivers forced structured verdict."""
        logger.info("[CIO Arbitrator] Delivering structured verdict")
        ticker = state.get("ticker", "")
        company_name = state.get("company_name", ticker)
        bull_outputs = state.get("bull_case_outputs", [])
        bear_outputs = state.get("bear_case_outputs", [])
        capital = state.get("capital", 10_000_000.0)
        risk_tolerance = state.get("risk_tolerance", "Moderate")
        current_price = state.get("current_price")
        price_timestamp = state.get("price_timestamp")
        if not current_price or current_price <= 0:
            try:
                from src.adapters.market_data.kobo_terminal import KoboTerminalAdapter
                adapter = KoboTerminalAdapter()
                quote = await adapter.get_quote(ticker)
                await adapter.close()
                if quote and quote.price > 0:
                    current_price = quote.price
                    price_timestamp = quote.timestamp
                    logger.info(f"[CIO Arbitrator] Fetched live market price for {ticker} from KoboTerminal: ₦{current_price} (timestamp: {price_timestamp})")
            except Exception as e:
                logger.warning(f"[CIO Arbitrator] Failed to fetch live price for {ticker}: {e}")

        full_bull = "\n\n".join([f"### Bull Case - Round {i+1}\n{o}" for i, o in enumerate(bull_outputs)])
        full_bear = "\n\n".join([f"### Bear Case - Round {i+1}\n{o}" for i, o in enumerate(bear_outputs)])

        system_prompt = build_agent_prompt(
            role=AgentRole.ARBITRATOR,
            ticker=ticker,
            company_name=company_name,
            bull_case_output=full_bull,
            bear_case_output=full_bear,
            financial_context=state.get("financial_context", []),
            capital=capital,
            risk_tolerance=risk_tolerance,
            current_price=current_price,
            verdict="",  # placeholder so Jinja doesn't error on undefined
        )

        tools = get_tools_for_role_objects("arbitrator")
        llm_with_tools = self.llm.bind_tools(tools)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Deliver final investment verdict for {company_name} ({ticker}) after {len(bull_outputs)} rounds of debate.")
        ]

        # Bounded tool execution loop (max 3 iterations)
        for _ in range(3):
            response = await llm_with_tools.ainvoke(messages)
            if hasattr(response, "tool_calls") and response.tool_calls:
                messages.append(response)
                for tc in response.tool_calls:
                    tool_fn = TOOL_MAP.get(tc["name"])
                    if tool_fn:
                        logger.info(f"[CIO Arbitrator] Tool called: {tc['name']} with args {tc['args']}")
                        try:
                            tool_result = await tool_fn.ainvoke(tc["args"])
                        except Exception as e:
                            logger.error(f"[CIO Arbitrator] Tool {tc['name']} error: {e}")
                            tool_result = {"error": str(e)}
                        messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))
                continue
            else:
                break

        # Force structured output using with_structured_output (strict contract, no regex fallback)
        structured_llm = self.llm.with_structured_output(ArbitratorResponse)
        try:
            structured_response: ArbitratorResponse = await structured_llm.ainvoke(messages)
        except Exception as e:
            logger.error(f"[CIO Arbitrator] Structured output validation failed: {e}")
            raise ValueError(f"Arbitration failed: LLM output did not conform to ArbitratorResponse schema: {e}")

        if not isinstance(structured_response, ArbitratorResponse):
            raise ValueError("Arbitration failed: Structured response is not an instance of ArbitratorResponse.")

        verdict = structured_response.verdict
        confidence = structured_response.confidence

        # Deterministic risk engine calculation for recommendation
        recommendation = calculate_recommendation(
            verdict=verdict,
            confidence=confidence,
            capital=capital,
            risk_tolerance=risk_tolerance,
            current_price=current_price,
            price_timestamp=price_timestamp
        )
        recommendation["key_risks"] = structured_response.unresolved_risks
        recommendation["key_catalysts"] = structured_response.bull_arguments_accepted

        output_content = structured_response.model_dump_json(indent=2)

        return {
            "arbitrator_output": output_content,
            "chat_response": structured_response.chat_response,
            "verdict": verdict,
            "recommendation": recommendation,
            "messages": [AIMessage(content=output_content, name="arbitrator")]
        }

    async def run_debate(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        user_thesis: Optional[str] = None,
        financial_context: Optional[List[Dict[str, Any]]] = None,
        capital: float = 10_000_000.0,
        risk_tolerance: str = "Moderate",
        current_price: Optional[float] = None,
        max_rounds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute MAD workflow.

        Returns:
            Dict with bull_case_history, bear_case_history, verdict, rounds_completed
        """
        initial_state: DebateState = {
            "ticker": ticker.upper(),
            "company_name": company_name or ticker.upper(),
            "user_thesis": user_thesis,
            "financial_context": financial_context or [],
            "capital": capital,
            "risk_tolerance": risk_tolerance,
            "current_price": current_price,
            "bull_case_outputs": [],
            "bear_case_outputs": [],
            "arbitrator_output": None,
            "chat_response": None,
            "messages": [],
            "metadata": {},
            "round_count": 0,
            "max_rounds": max_rounds or self.max_rounds,
            "next_agent": None,
        }

        logger.info(f"[Debate Engine] Starting MAD for {ticker.upper()} (max {initial_state['max_rounds']} rounds)")
        result_state = await self.workflow.ainvoke(initial_state)

        return {
            "ticker": result_state["ticker"],
            "company_name": result_state["company_name"],
            "bull_case_history": result_state.get("bull_case_outputs", []),
            "bear_case_history": result_state.get("bear_case_outputs", []),
            "verdict": result_state.get("verdict"),
            "recommendation": result_state.get("recommendation"),
            "arbitrator_output": result_state.get("arbitrator_output"),
            "chat_response": result_state.get("chat_response"),
            "rounds_completed": result_state.get("round_count", 0),
            "messages": result_state.get("messages", []),
            "metadata": result_state.get("metadata", {}),
        }


LangGraphMADEngine = LangGraphDebateEngine
