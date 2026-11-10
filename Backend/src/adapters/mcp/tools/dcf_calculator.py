"""MCP DCF Calculator Tool - Pure Python DCF valuation model with strict input validation."""

from langchain_core.tools import tool


@tool
async def run_dcf_model(
    fcf: float,
    growth_rate: float,
    wacc: float,
    terminal_growth: float,
    years: int = 5
) -> dict:
    """
    Runs a Discounted Cash Flow valuation model (pure Python calculation) with input validation.

    Args:
        fcf: Current Free Cash Flow in millions (₦) - must be > 0
        growth_rate: Expected annual FCF growth (e.g., 0.15 for 15%)
        wacc: Weighted Average Cost of Capital / discount rate (e.g., 0.15)
        terminal_growth: Perpetual growth rate (typically 0.02-0.03)
        years: Projection years (default 5, 1-50)

    Returns:
        {
            "intrinsic_value_millions": 420000,
            "pv_cash_flows": 280000,
            "pv_terminal_value": 140000,
            "projected_fcf": [180, 207, 238, 274, 315],
            "assumptions": {
                "growth_rate": 0.15,
                "terminal_growth": 0.03,
                "wacc": 0.15
            }
        }
    """
    if fcf is None or not isinstance(fcf, (int, float)) or fcf <= 0:
        raise ValueError("Invalid or missing FCF: must be a positive number in millions (₦)")

    if growth_rate is None or not isinstance(growth_rate, (int, float)) or not (-1.0 <= growth_rate <= 5.0):
        raise ValueError("Invalid growth_rate: must be between -1.0 (-100%) and 5.0 (500%)")

    if wacc is None or not isinstance(wacc, (int, float)) or not (0.0 < wacc < 2.0):
        raise ValueError("Invalid WACC: must be between 0.0 and 2.0 (exclusive of 0)")

    if terminal_growth is None or not isinstance(terminal_growth, (int, float)) or not (0.0 <= terminal_growth < wacc):
        raise ValueError("Invalid terminal_growth: must be non-negative and strictly less than WACC")

    if years is None or not isinstance(years, int) or not (1 <= years <= 50):
        raise ValueError("Invalid projection years: must be an integer between 1 and 50")

    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than terminal growth rate")

    projected_fcf = []
    discounted_fcf = []
    current_fcf = float(fcf)

    for year in range(1, years + 1):
        current_fcf = current_fcf * (1 + growth_rate)
        projected_fcf.append(round(current_fcf, 2))
        discount_factor = (1 + wacc) ** year
        discounted_fcf.append(current_fcf / discount_factor)

    pv_cash_flows = sum(discounted_fcf)

    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + wacc) ** years)

    intrinsic_value_millions = pv_cash_flows + pv_terminal_value

    return {
        "intrinsic_value_millions": round(intrinsic_value_millions, 2),
        "pv_cash_flows": round(pv_cash_flows, 2),
        "pv_terminal_value": round(pv_terminal_value, 2),
        "projected_fcf": projected_fcf,
        "assumptions": {
            "growth_rate": growth_rate,
            "terminal_growth": terminal_growth,
            "wacc": wacc
        }
    }
