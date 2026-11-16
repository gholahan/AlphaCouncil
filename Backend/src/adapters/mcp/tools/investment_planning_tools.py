"""
MCP Investment Planning Tools - Pure Python financial calculation tools for CIO Arbitrator.
"""

from langchain_core.tools import tool
from src.domain.services.investment_calculations import (
    calculate_transaction_costs,
    calculate_share_quantity,
    calculate_dividend_income,
    calculate_scenario_performance,
    calculate_entry_strategy,
)


@tool
async def calculate_investment_plan(
    allocation: float,
    entry_price: float,
    capital: float,
    verdict: str,
    exchange: str = "NGX",
    annual_dps: float = 0.0,
    years: int = 2,
    bear_target_price: float = 0.0,
    base_target_price: float = 0.0,
    bull_target_price: float = 0.0,
) -> dict:
    """
    Deterministically calculates transaction costs, whole share quantity, remaining cash,
    entry strategy, and expected performance scenarios (Bear, Base, Bull) for the investment report.

    Args:
        allocation: Recommended capital allocation in currency (₦)
        entry_price: Current market price or entry price
        capital: Total investor available capital
        verdict: Final verdict (Strong Buy, Buy, Hold, Sell, Strong Sell)
        exchange: Exchange code (default "NGX")
        annual_dps: Annual dividend per share (optional)
        years: Investment horizon in years (default 2)
        bear_target_price: Projected bear case price
        base_target_price: Projected base case price
        bull_target_price: Projected bull case price

    Returns:
        Dict containing transaction costs, shares, remaining cash, entry strategy, and scenarios.
    """
    costs = calculate_transaction_costs(allocation, exchange)
    total_costs = costs["total_costs"]
    shares = calculate_share_quantity(allocation, entry_price, total_costs)
    actual_allocation = shares * entry_price + total_costs
    remaining_cash = max(0.0, capital - actual_allocation)

    entry_strat = calculate_entry_strategy(entry_price, verdict)

    # Default targets if not supplied
    bear = bear_target_price if bear_target_price > 0 else entry_price * 0.85
    base = base_target_price if base_target_price > 0 else entry_price * 1.30
    bull = bull_target_price if bull_target_price > 0 else entry_price * 1.55

    scenario_prices = {
        "Bear Case": bear,
        "Base Case": base,
        "Bull Case": bull,
    }

    dividend_income = calculate_dividend_income(shares, annual_dps, years)
    scenarios = calculate_scenario_performance(entry_price, shares, scenario_prices, dividend_income, float(years))

    allocation_pct = round((actual_allocation / capital) * 100.0, 2) if capital > 0 else 0.0

    return {
        "allocation": round(actual_allocation, 2),
        "allocation_percentage": allocation_pct,
        "number_shares": shares,
        "estimated_transaction_costs": total_costs,
        "cost_breakdown": costs,
        "remaining_cash": round(remaining_cash, 2),
        "entry_strategy": entry_strat,
        "scenarios": scenarios,
    }
