import math
from typing import Dict, Any, List, Optional


def calculate_transaction_costs(allocation: float, exchange: str = "NGX") -> Dict[str, float]:
    """
    Calculate applicable transaction costs for an equity trade.
    For NGX (Nigerian Exchange), standard statutory and broker fees apply:
    - SEC Fee: 0.3%
    - NSE Fee: 0.02%
    - CSCS Fee: 0.03%
    - Broker Commission: up to 1.35% (default 1.35%)
    Total default fee rate for NGX approx ~1.7%.
    """
    if allocation <= 0:
        return {"sec_fee": 0.0, "nse_fee": 0.0, "cscs_fee": 0.0, "broker_commission": 0.0, "total_costs": 0.0}

    ex = exchange.strip().upper()
    if ex == "NGX":
        sec_fee = allocation * 0.003
        nse_fee = allocation * 0.0002
        cscs_fee = allocation * 0.0003
        broker_commission = allocation * 0.0135
        total_costs = sec_fee + nse_fee + cscs_fee + broker_commission
        return {
            "sec_fee": round(sec_fee, 2),
            "nse_fee": round(nse_fee, 2),
            "cscs_fee": round(cscs_fee, 2),
            "broker_commission": round(broker_commission, 2),
            "total_costs": round(total_costs, 2),
        }
    else:
        total_costs = allocation * 0.005
        return {
            "sec_fee": 0.0,
            "nse_fee": 0.0,
            "cscs_fee": 0.0,
            "broker_commission": round(total_costs, 2),
            "total_costs": round(total_costs, 2),
        }


def calculate_share_quantity(allocation: float, entry_price: float, total_costs: float) -> int:
    """
    Calculate whole shares purchasable within the recommended allocation and costs.
    Formula: floor((Allocation - Costs) / Entry Price)
    """
    if allocation <= 0 or entry_price <= 0:
        return 0

    net_capital = allocation - total_costs
    if net_capital <= 0:
        return 0

    shares = math.floor(net_capital / entry_price)
    return max(0, int(shares))


def calculate_dividend_income(shares: int, annual_dps: float, years: int, dps_growth_rate: float = 0.05) -> float:
    """
    Estimate cumulative dividend income over the investment horizon,
    accounting for annual dividend growth.
    """
    if shares <= 0 or annual_dps <= 0 or years <= 0:
        return 0.0

    total_dividends = 0.0
    current_dps = float(annual_dps)
    for _ in range(int(years)):
        total_dividends += shares * current_dps
        current_dps *= (1.0 + dps_growth_rate)

    return round(total_dividends, 2)


def calculate_annualized_return(start_value: float, end_value: float, years: float) -> float:
    """
    Calculate Compound Annual Growth Rate (CAGR).
    """
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0

    try:
        cagr = (end_value / start_value) ** (1.0 / years) - 1.0
        return round(cagr * 100.0, 2)
    except Exception:
        return 0.0


def calculate_scenario_performance(
    entry_price: float,
    shares: int,
    scenario_prices: Dict[str, float],
    dividend_income: float,
    years: float,
    probabilities: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Calculate bear, base, and bull case performance scenarios.
    Returns list of scenario performance dicts (maintaining backward compatibility for tests).
    """
    if probabilities is None:
        probabilities = {"Bear Case": 0.20, "Base Case": 0.50, "Bull Case": 0.30}

    initial_investment = shares * entry_price
    results = []

    for scenario_name, target_price in scenario_prices.items():
        ending_share_value = shares * target_price
        total_ending_value = ending_share_value + dividend_income
        capital_gain_loss = ending_share_value - initial_investment
        capital_gain_loss_pct = (capital_gain_loss / initial_investment * 100.0) if initial_investment > 0 else 0.0
        total_return = total_ending_value - initial_investment
        total_return_pct = (total_return / initial_investment * 100.0) if initial_investment > 0 else 0.0
        cagr = calculate_annualized_return(initial_investment, total_ending_value, years)

        results.append({
            "scenario_name": scenario_name,
            "scenario_share_price": round(target_price, 2),
            "capital_gain_loss_amount": round(capital_gain_loss, 2),
            "capital_gain_loss_percent": round(capital_gain_loss_pct, 2),
            "expected_dividend_income": round(dividend_income, 2),
            "total_investment_value": round(total_ending_value, 2),
            "total_return_percent": round(total_return_pct, 2),
            "annualized_return_cagr": cagr,
            "probability": probabilities.get(scenario_name, 0.33),
        })

    return results


def calculate_entry_strategy(current_price: float, verdict: str) -> Dict[str, Any]:
    """
    Evaluate entry-price ranges and staged-entry recommendations based on verdict.
    """
    v = verdict.strip().title()
    if v in ["Strong Buy", "Buy"]:
        return {
            "entry_range_min": round(current_price * 0.95, 2),
            "entry_range_max": round(current_price * 1.02, 2),
            "execution_strategy": "Staged entry: deploy 50% immediately at current market price and 50% on minor pullbacks.",
        }
    elif v == "Hold":
        return {
            "entry_range_min": round(current_price * 0.90, 2),
            "entry_range_max": round(current_price * 0.98, 2),
            "execution_strategy": "Wait for a more attractive entry price or accumulate only on weakness.",
        }
    else:
        return {
            "entry_range_min": 0.0,
            "entry_range_max": 0.0,
            "execution_strategy": "Avoid new purchases; consider reducing or exiting existing positions.",
        }
