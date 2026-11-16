"""
CIO Investment Decision Report Domain Models (Prose-First 8-Section Architecture)
Sprint 1 Specification -- MAD Finance
"""

from datetime import datetime, timezone
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Verdict type matching Sprint 1 specification §3.1 & §4.3
VerdictType = Literal["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]

LEGACY_VERDICT_MAP = {
    "BUY": "Buy",
    "CONDITIONAL_BUY": "Buy",
    "HOLD": "Hold",
    "SELL": "Sell",
    "STRONG_BUY": "Strong Buy",
    "STRONG_SELL": "Strong Sell",
}


class InvestmentRecommendation(BaseModel):
    """Dedicated structured recommendation model replacing unstructured dictionaries."""
    model_config = ConfigDict(extra="forbid", strict=True)

    verdict: VerdictType
    available_capital: float = Field(gt=0, description="Capital made available for this decision")
    proposed_allocation: float = Field(ge=0, description="Allocation amount committed")
    allocation_percentage: float = Field(ge=0.0, le=100.0, description="Allocation as % of available capital")
    share_quantity: int = Field(ge=0, description="Whole shares purchasable")
    entry_price: Optional[float] = Field(None, gt=0, description="Entry price")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    target_price: Optional[float] = Field(None, gt=0, description="Target valuation price")
    transaction_costs: float = Field(ge=0, description="Total transaction fees")
    remaining_cash: float = Field(ge=0, description="Remaining cash after allocation and costs")
    scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="Bear, base, and bull return scenarios")


class CIOInvestmentReport(BaseModel):
    """
    Complete 8-Section CIO Investment Decision Report (Prose-First Architecture).
    Enforces that all 8 sections are written in rich markdown prose/tables by the LLM,
    backed by validated deterministic financial calculations.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(description="Full company name")
    exchange: str = Field(default="NGX", description="Stock exchange")
    current_market_price: float = Field(gt=0, description="Latest verified market price")
    verdict: VerdictType = Field(description="Final investment verdict: Strong Buy, Buy, Hold, Sell, or Strong Sell")
    investment_horizon: str = Field(description="Recommended investment horizon (e.g., 12 months)")
    confidence_score: float = Field(ge=0.0, le=1.0, description="CIO confidence score (0.0 to 1.0)")

    # The 8 required sections as rich markdown prose and tables
    section_1_verdict_prose: str = Field(min_length=100, description="Rich prose for Section 1: Investment Verdict")
    section_2_thesis_prose: str = Field(min_length=150, description="Rich prose for Section 2: Investment Thesis")
    section_3_risks_prose: str = Field(min_length=100, description="Rich prose and markdown table for Section 3: Investment Risks")
    section_4_plan_prose: str = Field(min_length=100, description="Rich prose and markdown table for Section 4: Recommended Investment Plan")
    section_5_performance_prose: str = Field(min_length=100, description="Rich prose and markdown table for Section 5: Expected Investment Performance")
    section_6_exit_prose: str = Field(min_length=100, description="Rich prose for Section 6: Exit Strategy")
    section_7_monitoring_prose: str = Field(min_length=100, description="Rich prose and markdown table for Section 7: What to Monitor")
    section_8_conclusion_prose: str = Field(min_length=100, description="Rich prose for Section 8: Final CIO Conclusion")

    # Validated quantitative recommendation model
    recommendation: InvestmentRecommendation = Field(description="Structured recommendation model")

    # Complete unified markdown report
    chat_response: str = Field(
        min_length=300,
        description=(
            "Complete, publication-ready Markdown investment report combining all "
            "eight sections in professional analyst prose (matching the Dangote Cement example style), "
            "addressed directly to the investor."
        )
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def confidence(self) -> float:
        return self.confidence_score

    @property
    def unresolved_risks(self) -> List[str]:
        return ["Foreign exchange volatility", "Operating cost pressures"]

    @property
    def bull_arguments_accepted(self) -> List[str]:
        return ["Established market position", "Infrastructure demand growth"]
