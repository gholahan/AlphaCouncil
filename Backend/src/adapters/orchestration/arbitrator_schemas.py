"""Arbitrator Pydantic schema and deterministic risk-based position sizing calculations."""

from datetime import datetime, timezone
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ArbitratorResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )
    verdict: Literal["BUY", "CONDITIONAL_BUY", "HOLD", "SELL"]
    investment_thesis: str = Field(min_length=30)
    valuation_assessment: str
    time_horizon: str
    rationale: str = Field(min_length=30)
    bull_arguments_accepted: List[str]
    bear_arguments_accepted: List[str]
    unresolved_risks: List[str]
    conditions_that_would_change_verdict: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    monitoring_triggers: List[str] = Field(default_factory=list)
    dissenting_opinion: Optional[str] = None
    chat_response: str = Field(
        min_length=100,
        description=(
            "Complete, natural conversational investment "
            "analysis addressed directly to the investor. "
            "Follow the required MAD Finance CIO response "
            "structure and use the same validated figures "
            "and verdict as the structured fields."
        )
    )


def calculate_recommendation(
    verdict: str,
    confidence: float,
    capital: float,
    risk_tolerance: str,
    current_price: float,
    price_timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Risk-based position sizing calculation:
    1. Validate capital, verdict, risk tolerance, and current_price (no ₦100 fallback).
    2. Validate market-price freshness if price_timestamp is provided.
    3. Risk Budget = Capital * Risk Percentage (based on normalized risk tolerance & verdict).
    4. Stop Loss Price & Risk Per Share.
    5. Position Size (Shares) = floor(Risk Budget / Risk Per Share).
    6. Allocation = Shares * Entry Price.
    7. Enforce independent maximum capital allocation cap.
    """
    if capital <= 0:
        raise ValueError("Capital must be greater than 0")

    if current_price is None or current_price <= 0:
        raise ValueError("current_price is required and must be greater than 0 (no fallback allowed)")
    price = float(current_price)

    if price_timestamp:
        ts = price_timestamp if price_timestamp.tzinfo else price_timestamp.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_hours = (now - ts).total_seconds() / 3600.0
        if age_hours > 72.0:
            raise ValueError(f"Market price is stale: timestamp {ts.isoformat()} is {age_hours:.1f} hours old (max allowed: 72h)")

    if not risk_tolerance:
        raise ValueError("risk_tolerance is required")

    normalized_rt = str(risk_tolerance).strip().capitalize()
    valid_risk_pcts = {"Conservative": 0.01, "Moderate": 0.02, "Aggressive": 0.03}
    valid_max_allocs = {"Conservative": 0.25, "Moderate": 0.50, "Aggressive": 0.90}

    if normalized_rt not in valid_risk_pcts:
        raise ValueError(f"Invalid risk tolerance: '{risk_tolerance}'. Must be Conservative, Moderate, or Aggressive.")

    valid_verdicts = {"BUY", "CONDITIONAL_BUY", "HOLD", "SELL"}
    normalized_verdict = str(verdict).strip().upper()
    if normalized_verdict not in valid_verdicts:
        raise ValueError(f"Invalid verdict: '{verdict}'. Must be BUY, CONDITIONAL_BUY, HOLD, or SELL.")

    base_risk_pct = valid_risk_pcts[normalized_rt]
    verdict_risk_mult = {"BUY": 1.0, "CONDITIONAL_BUY": 0.5, "HOLD": 0.1, "SELL": 0.0}[normalized_verdict]
    risk_percentage = base_risk_pct * verdict_risk_mult

    risk_budget = capital * risk_percentage

    # Stop loss price (15% drop for BUY/CONDITIONAL_BUY, 5% for HOLD, 1% for SELL)
    stop_drop = 0.15 if normalized_verdict in ["BUY", "CONDITIONAL_BUY"] else (0.05 if normalized_verdict == "HOLD" else 0.01)
    stop_price = price * (1.0 - stop_drop)
    risk_per_share = price - stop_price

    if risk_per_share > 0 and risk_budget > 0:
        shares = int(risk_budget / risk_per_share)
    else:
        shares = 0

    allocation = shares * price

    # Enforce maximum capital allocation independently of the risk budget
    max_alloc_pct = valid_max_allocs[normalized_rt]
    verdict_alloc_mult = {"BUY": 1.0, "CONDITIONAL_BUY": 0.5, "HOLD": 0.1, "SELL": 0.0}[normalized_verdict]
    max_allowed_allocation = capital * max_alloc_pct * verdict_alloc_mult

    if allocation > max_allowed_allocation:
        allocation = max_allowed_allocation
        shares = int(allocation / price) if price > 0 else 0

    target_price = price * (1.35 if normalized_verdict == "BUY" else (1.15 if normalized_verdict == "CONDITIONAL_BUY" else 1.05))

    return {
        "allocation": round(allocation, 2),
        "position_size": shares,
        "stop_loss": round(stop_price, 2),
        "target_price": round(target_price, 2),
        "confidence": confidence,
    }
