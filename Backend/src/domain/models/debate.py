"""Domain models for investment debates."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class DebateTurn:
    """Core domain representation of a single agent's argument turn."""
    agent_role: str
    turn_number: int
    content: str
    citations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DebateVerdict:
    """Core domain representation of the CIO Arbitrator's final verdict."""
    verdict: str  # "BUY", "CONDITIONAL_BUY", "HOLD", "SELL"
    recommendation: Dict[str, Any] = field(default_factory=dict)
    rationale: Optional[str] = None
    dissenting_opinion: Optional[str] = None


@dataclass
class InvestmentDebate:
    """Core domain aggregate root for an investment debate session."""
    ticker: str
    company_name: str
    user_thesis: Optional[str] = None
    capital_to_deploy: float = 10_000_000.0
    risk_tolerance: str = "Moderate"
    current_price: Optional[float] = None
    bull_case_outputs: List[str] = field(default_factory=list)
    bear_case_outputs: List[str] = field(default_factory=list)
    arbitrator_output: Optional[str] = None
    final_verdict: Optional[DebateVerdict] = None
    rounds_completed: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
