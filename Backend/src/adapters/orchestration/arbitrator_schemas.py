"""Arbitrator Pydantic schema and deterministic risk-based position sizing calculations."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from src.domain.models.cio_report import CIOInvestmentReport, VerdictType, LEGACY_VERDICT_MAP


class ArbitratorResponse(CIOInvestmentReport):
    """
    ArbitratorResponse inherits from CIOInvestmentReport to ensure the CIO
    produces the complete 8-section report along with chat response.
    """
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    @field_validator("verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, v: Any) -> Any:
        if isinstance(v, str):
            raw_v = v.strip()
            if raw_v.upper() in LEGACY_VERDICT_MAP:
                return LEGACY_VERDICT_MAP[raw_v.upper()]
            return raw_v.title()
        return v


def calculate_recommendation(
    verdict: str,
    confidence: float,
    capital: float,
    risk_tolerance: str,
    current_price: float,
    price_timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Risk-based position sizing calculation supporting 5 Sprint 1 verdicts:
    Strong Buy, Buy, Hold, Sell, Strong Sell.
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

    # Normalize verdict string
    raw_v = str(verdict).strip()
    if raw_v.upper() in LEGACY_VERDICT_MAP:
        norm_verdict = LEGACY_VERDICT_MAP[raw_v.upper()]
    else:
        norm_verdict = raw_v.title()

    valid_verdicts = {"Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"}
    if norm_verdict not in valid_verdicts:
        raise ValueError(f"Invalid verdict: '{verdict}'. Must be Strong Buy, Buy, Hold, Sell, or Strong Sell.")

    base_risk_pct = valid_risk_pcts[normalized_rt]

    risk_multipliers = {
        "Strong Buy": 1.25,
        "Buy": 1.0,
        "Hold": 0.1,
        "Sell": 0.0,
        "Strong Sell": 0.0,
    }
    alloc_multipliers = {
        "Strong Buy": 1.0,
        "Buy": 0.75,
        "Hold": 0.10,
        "Sell": 0.0,
        "Strong Sell": 0.0,
    }

    verdict_risk_mult = risk_multipliers[norm_verdict]
    risk_percentage = base_risk_pct * verdict_risk_mult
    risk_budget = capital * risk_percentage

    stop_drops = {
        "Strong Buy": 0.15,
        "Buy": 0.15,
        "Hold": 0.05,
        "Sell": 0.01,
        "Strong Sell": 0.01,
    }
    stop_drop = stop_drops[norm_verdict]
    stop_price = price * (1.0 - stop_drop)
    risk_per_share = price - stop_price

    if risk_per_share > 0 and risk_budget > 0:
        shares = int(risk_budget / risk_per_share)
    else:
        shares = 0

    allocation = shares * price

    max_alloc_pct = valid_max_allocs[normalized_rt]
    verdict_alloc_mult = alloc_multipliers[norm_verdict]
    max_allowed_allocation = capital * max_alloc_pct * verdict_alloc_mult

    if allocation > max_allowed_allocation:
        allocation = max_allowed_allocation
        shares = int(allocation / price) if price > 0 else 0

    target_multipliers = {
        "Strong Buy": 1.45,
        "Buy": 1.30,
        "Hold": 1.08,
        "Sell": 0.95,
        "Strong Sell": 0.85,
    }
    target_price = price * target_multipliers[norm_verdict]

    return {
        "verdict": norm_verdict,
        "allocation": round(allocation, 2),
        "position_size": shares,
        "stop_loss": round(stop_price, 2),
        "target_price": round(target_price, 2),
        "confidence": confidence,
    }
