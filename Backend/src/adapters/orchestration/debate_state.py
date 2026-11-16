"""Debate State - State definitions for LangGraph multi-agent financial debate with additive operators."""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
from operator import add
from langchain_core.messages import BaseMessage


class DebateState(TypedDict):
    """State graph structure for the investment debate workflow with accumulation."""

    ticker: str
    company_name: str
    user_thesis: Optional[str]
    financial_context: List[Dict[str, Any]]
    capital: float
    risk_tolerance: str
    current_price: Optional[float]
    price_timestamp: Optional[Any]
    exchange: Optional[str]

    # Accumulated outputs (preserves history across rounds)
    bull_case_outputs: Annotated[List[str], add]
    bear_case_outputs: Annotated[List[str], add]
    arbitrator_output: Optional[str]
    chat_response: Optional[str]
    cio_report: Optional[Dict[str, Any]]

    # Structured final verdict and recommendation
    verdict: Optional[str]  # "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
    recommendation: Optional[Dict[str, Any]]  # {allocation, position_size, stop_loss, target_price, confidence, key_risks, key_catalysts}

    # Message history (accumulated)
    messages: Annotated[List[BaseMessage], add]

    # Metadata (merged)
    metadata: Dict[str, Any]

    # Supervisor state
    round_count: int
    max_rounds: int
    next_agent: Optional[str]
