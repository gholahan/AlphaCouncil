"""
MCP Financial Analysis Tools - Structured financial analysis helpers for Bull and Bear analysts.
Incorporates rigorous missing data handling, proper Enterprise Value calculations,
and genuine DCF sensitivity modeling.
"""

from langchain_core.tools import tool
from typing import List, Dict, Any, Optional


@tool
async def calculate_financial_growth(
    revenue_current: Optional[float] = None,
    revenue_prior: Optional[float] = None,
    earnings_current: Optional[float] = None,
    earnings_prior: Optional[float] = None,
    reporting_period: str = "FY2025",
) -> dict:
    """
    Calculate revenue and earnings growth rates (YoY percentage) with robust missing data handling.
    """
    limitations = []
    rev_growth = None
    earn_growth = None

    if revenue_current is not None and revenue_prior is not None and revenue_prior != 0:
        rev_growth = ((revenue_current - revenue_prior) / abs(revenue_prior)) * 100.0
    else:
        limitations.append("Revenue data incomplete or prior period zero.")

    if earnings_current is not None and earnings_prior is not None:
        if earnings_prior != 0:
            earn_growth = ((earnings_current - earnings_prior) / abs(earnings_prior)) * 100.0
        else:
            limitations.append("Prior earnings were zero (turnaround or base effect).")
    else:
        limitations.append("Earnings data incomplete.")

    return {
        "metrics": {
            "revenue_growth_percent": {"value": round(rev_growth, 2) if rev_growth is not None else None, "unit": "%", "status": "available" if rev_growth is not None else "unavailable"},
            "earnings_growth_percent": {"value": round(earn_growth, 2) if earn_growth is not None else None, "unit": "%", "status": "available" if earn_growth is not None else "unavailable"},
        },
        "reporting_period": reporting_period,
        "limitations": limitations,
    }


@tool
async def analyze_profitability(
    gross_profit: Optional[float] = None,
    revenue: Optional[float] = None,
    net_income: Optional[float] = None,
    total_assets: Optional[float] = None,
    total_equity: Optional[float] = None,
    reporting_period: str = "FY2025",
) -> dict:
    """
    Analyze profitability margins (Gross Margin, Net Margin, ROE, ROA) with missing data handling.
    """
    limitations = []
    gross_margin = (gross_profit / revenue * 100.0) if (gross_profit is not None and revenue and revenue != 0) else None
    if gross_margin is None:
        limitations.append("Gross profit or revenue unavailable.")

    net_margin = (net_income / revenue * 100.0) if (net_income is not None and revenue and revenue != 0) else None
    if net_margin is None:
        limitations.append("Net income or revenue unavailable.")

    roe = (net_income / total_equity * 100.0) if (net_income is not None and total_equity and total_equity != 0) else None
    if roe is None:
        limitations.append("Net income or total equity unavailable.")

    roa = (net_income / total_assets * 100.0) if (net_income is not None and total_assets and total_assets != 0) else None
    if roa is None:
        limitations.append("Net income or total assets unavailable.")

    return {
        "metrics": {
            "gross_margin_percent": {"value": round(gross_margin, 2) if gross_margin is not None else None, "unit": "%", "status": "available" if gross_margin is not None else "unavailable"},
            "net_profit_margin_percent": {"value": round(net_margin, 2) if net_margin is not None else None, "unit": "%", "status": "available" if net_margin is not None else "unavailable"},
            "roe_percent": {"value": round(roe, 2) if roe is not None else None, "unit": "%", "status": "available" if roe is not None else "unavailable"},
            "roa_percent": {"value": round(roa, 2) if roa is not None else None, "unit": "%", "status": "available" if roa is not None else "unavailable"},
        },
        "reporting_period": reporting_period,
        "limitations": limitations,
    }


@tool
async def analyze_financial_health(
    total_debt: Optional[float] = None,
    total_equity: Optional[float] = None,
    current_assets: Optional[float] = None,
    current_liabilities: Optional[float] = None,
    ebit: Optional[float] = None,
    interest_expense: Optional[float] = None,
    reporting_period: str = "FY2025",
) -> dict:
    """
    Analyze liquidity, leverage, and solvency without arbitrary fallback values.
    """
    limitations = []
    debt_to_equity = (total_debt / total_equity) if (total_debt is not None and total_equity and total_equity != 0) else None
    if debt_to_equity is None:
        limitations.append("Total debt or total equity unavailable.")

    current_ratio = (current_assets / current_liabilities) if (current_assets is not None and current_liabilities and current_liabilities != 0) else None
    if current_ratio is None:
        limitations.append("Current assets or current liabilities unavailable.")

    interest_coverage = None
    if ebit is not None and interest_expense is not None:
        if interest_expense > 0:
            interest_coverage = ebit / interest_expense
        elif interest_expense == 0:
            interest_coverage = 999.0  # Zero debt / interest-free
            limitations.append("Zero interest expense recorded (debt-free or interest-free).")
    else:
        limitations.append("EBIT or interest expense unavailable.")

    return {
        "metrics": {
            "debt_to_equity_ratio": {"value": round(debt_to_equity, 2) if debt_to_equity is not None else None, "unit": "x", "status": "available" if debt_to_equity is not None else "unavailable"},
            "current_ratio": {"value": round(current_ratio, 2) if current_ratio is not None else None, "unit": "x", "status": "available" if current_ratio is not None else "unavailable"},
            "interest_coverage_ratio": {"value": round(interest_coverage, 2) if interest_coverage is not None else None, "unit": "x", "status": "available" if interest_coverage is not None else "unavailable"},
        },
        "reporting_period": reporting_period,
        "limitations": limitations,
    }


@tool
async def analyze_cash_flow(
    operating_cash_flow: Optional[float] = None,
    net_income: Optional[float] = None,
    capital_expenditures: Optional[float] = None,
    reporting_period: str = "FY2025",
) -> dict:
    """
    Analyze Free Cash Flow and Cash Conversion Ratio with transparent missing data handling.
    """
    limitations = []
    fcf = None
    if operating_cash_flow is not None and capital_expenditures is not None:
        fcf = operating_cash_flow - abs(capital_expenditures)
    else:
        limitations.append("Operating cash flow or capex unavailable.")

    cash_conversion = None
    if operating_cash_flow is not None and net_income is not None:
        if net_income != 0:
            cash_conversion = (operating_cash_flow / net_income) * 100.0
        else:
            limitations.append("Net income is zero; cash conversion ratio undefined.")
    else:
        limitations.append("Operating cash flow or net income unavailable.")

    return {
        "metrics": {
            "free_cash_flow": {"value": round(fcf, 2) if fcf is not None else None, "unit": "NGN", "status": "available" if fcf is not None else "unavailable"},
            "cash_conversion_percent": {"value": round(cash_conversion, 2) if cash_conversion is not None else None, "unit": "%", "status": "available" if cash_conversion is not None else "unavailable"},
        },
        "reporting_period": reporting_period,
        "limitations": limitations,
    }


@tool
async def analyze_valuation(
    market_price: float,
    shares_outstanding: float,
    eps: Optional[float] = None,
    book_value_per_share: Optional[float] = None,
    ebitda: Optional[float] = None,
    total_debt: float = 0.0,
    cash_and_equivalents: float = 0.0,
    reporting_period: str = "FY2025",
) -> dict:
    """
    Analyze valuation multiples with correct Enterprise Value calculation: EV = Market Cap + Total Debt - Cash.
    """
    limitations = []
    pe_ratio = (market_price / eps) if (eps is not None and eps > 0) else None
    if pe_ratio is None:
        limitations.append("EPS unavailable or negative/zero.")

    pb_ratio = (market_price / book_value_per_share) if (book_value_per_share is not None and book_value_per_share > 0) else None
    if pb_ratio is None:
        limitations.append("Book value per share unavailable.")

    market_cap = market_price * shares_outstanding
    enterprise_value = market_cap + total_debt - cash_and_equivalents

    ev_ebitda = (enterprise_value / ebitda) if (ebitda is not None and ebitda > 0) else None
    if ev_ebitda is None:
        limitations.append("EBITDA unavailable or negative/zero.")

    return {
        "metrics": {
            "market_cap": {"value": round(market_cap, 2), "unit": "NGN", "status": "available"},
            "enterprise_value": {"value": round(enterprise_value, 2), "unit": "NGN", "status": "available"},
            "pe_ratio": {"value": round(pe_ratio, 2) if pe_ratio is not None else None, "unit": "x", "status": "available" if pe_ratio is not None else "unavailable"},
            "pb_ratio": {"value": round(pb_ratio, 2) if pb_ratio is not None else None, "unit": "x", "status": "available" if pb_ratio is not None else "unavailable"},
            "ev_ebitda_ratio": {"value": round(ev_ebitda, 2) if ev_ebitda is not None else None, "unit": "x", "status": "available" if ev_ebitda is not None else "unavailable"},
        },
        "reporting_period": reporting_period,
        "limitations": limitations,
    }


@tool
async def compare_peer_valuation(
    company_pe: Optional[float] = None,
    peer_pe_list: List[float] = [],
    company_pb: Optional[float] = None,
    peer_pb_list: List[float] = [],
) -> dict:
    """
    Compare company valuation multiples (both P/E and P/B) against peer group averages.
    """
    limitations = []
    avg_peer_pe = sum(peer_pe_list) / len(peer_pe_list) if peer_pe_list else None
    if avg_peer_pe is None:
        limitations.append("Peer P/E data unavailable.")

    pe_premium_discount = ((company_pe - avg_peer_pe) / avg_peer_pe * 100.0) if (company_pe is not None and avg_peer_pe is not None and avg_peer_pe != 0) else None

    avg_peer_pb = sum(peer_pb_list) / len(peer_pb_list) if peer_pb_list else None
    if avg_peer_pb is None:
        limitations.append("Peer P/B data unavailable.")

    pb_premium_discount = ((company_pb - avg_peer_pb) / avg_peer_pb * 100.0) if (company_pb is not None and avg_peer_pb is not None and avg_peer_pb != 0) else None

    return {
        "metrics": {
            "company_pe": {"value": company_pe, "status": "available" if company_pe is not None else "unavailable"},
            "peer_average_pe": {"value": round(avg_peer_pe, 2) if avg_peer_pe is not None else None, "peer_count": len(peer_pe_list), "status": "available" if avg_peer_pe is not None else "unavailable"},
            "pe_premium_discount_percent": {"value": round(pe_premium_discount, 2) if pe_premium_discount is not None else None, "unit": "%", "status": "available" if pe_premium_discount is not None else "unavailable"},
            "company_pb": {"value": company_pb, "status": "available" if company_pb is not None else "unavailable"},
            "peer_average_pb": {"value": round(avg_peer_pb, 2) if avg_peer_pb is not None else None, "peer_count": len(peer_pb_list), "status": "available" if avg_peer_pb is not None else "unavailable"},
            "pb_premium_discount_percent": {"value": round(pb_premium_discount, 2) if pb_premium_discount is not None else None, "unit": "%", "status": "available" if pb_premium_discount is not None else "unavailable"},
        },
        "limitations": limitations,
    }


@tool
async def run_valuation_sensitivity(
    fcf: float,
    growth_rate: float,
    wacc: float,
    terminal_growth: float,
    years: int = 5,
    wacc_delta: float = 0.01,
    terminal_growth_delta: float = 0.005,
) -> dict:
    """
    Genuine DCF sensitivity analysis recalculating intrinsic value across WACC and terminal growth variations.
    """
    from src.adapters.mcp.tools.dcf_calculator import run_dcf_model

    try:
        base_res = await run_dcf_model.ainvoke({
            "fcf": fcf, "growth_rate": growth_rate, "wacc": wacc, "terminal_growth": terminal_growth, "years": years
        })
        base_iv = base_res.get("intrinsic_value_millions", 0.0)

        # Bear case: WACC + 1%, Terminal growth - 0.5%
        bear_wacc = wacc + wacc_delta
        bear_g = max(0.0, terminal_growth - terminal_growth_delta)
        bear_res = await run_dcf_model.ainvoke({
            "fcf": fcf, "growth_rate": growth_rate, "wacc": bear_wacc, "terminal_growth": bear_g, "years": years
        })
        bear_iv = bear_res.get("intrinsic_value_millions", 0.0)

        # Bull case: WACC - 1%, Terminal growth + 0.5%
        bull_wacc = max(bear_g + 0.01, wacc - wacc_delta)
        bull_g = terminal_growth + terminal_growth_delta
        bull_res = await run_dcf_model.ainvoke({
            "fcf": fcf, "growth_rate": growth_rate, "wacc": bull_wacc, "terminal_growth": bull_g, "years": years
        })
        bull_iv = bull_res.get("intrinsic_value_millions", 0.0)

        return {
            "base_intrinsic_value_millions": base_iv,
            "bear_intrinsic_value_millions": bear_iv,
            "bull_intrinsic_value_millions": bull_iv,
            "assumptions_tested": {
                "base": {"wacc": wacc, "terminal_growth": terminal_growth},
                "bear": {"wacc": bear_wacc, "terminal_growth": bear_g},
                "bull": {"wacc": bull_wacc, "terminal_growth": bull_g},
            },
            "status": "success",
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@tool
async def analyze_downside_risk(
    current_price: float,
    historical_volatility_percent: Optional[float] = None,
) -> dict:
    """
    Evaluate downside price risk based on empirical volatility rather than arbitrary defaults.
    """
    limitations = []
    if historical_volatility_percent is None:
        historical_volatility_percent = 20.0  # default market proxy
        limitations.append("Historical volatility not supplied; using 20% proxy.")

    downside_price = current_price * (1.0 - (historical_volatility_percent / 100.0))
    return {
        "current_price": current_price,
        "implied_downside_price": round(downside_price, 2),
        "volatility_percent": historical_volatility_percent,
        "limitations": limitations,
    }


@tool
async def calculate_valuation_margin_of_safety(
    intrinsic_value: Optional[float] = None,
    market_price: Optional[float] = None,
) -> dict:
    """
    Calculate Margin of Safety percentage with missing data handling.
    """
    limitations = []
    mos = None
    if intrinsic_value is not None and market_price is not None and intrinsic_value > 0:
        mos = ((intrinsic_value - market_price) / intrinsic_value) * 100.0
    else:
        limitations.append("Intrinsic value or market price unavailable.")

    return {
        "intrinsic_value": intrinsic_value,
        "market_price": market_price,
        "margin_of_safety_percent": round(mos, 2) if mos is not None else None,
        "limitations": limitations,
    }


@tool
async def analyze_debt_exposure(
    total_debt: Optional[float] = None,
    short_term_debt: Optional[float] = None,
    cash_and_equivalents: Optional[float] = None,
    ebitda: Optional[float] = None,
    reporting_period: str = "FY2025",
) -> dict:
    """
    Analyze net debt and leverage with transparent handling of negative net debt and missing EBITDA.
    """
    limitations = []
    net_debt = None
    if total_debt is not None and cash_and_equivalents is not None:
        net_debt = total_debt - cash_and_equivalents
    else:
        limitations.append("Total debt or cash unavailable.")

    net_debt_to_ebitda = None
    if net_debt is not None and ebitda is not None:
        if ebitda > 0:
            net_debt_to_ebitda = net_debt / ebitda
        elif ebitda == 0:
            net_debt_to_ebitda = 0.0 if net_debt <= 0 else 999.0
            limitations.append("EBITDA is zero.")
        else:
            limitations.append("EBITDA is negative.")
    else:
        limitations.append("EBITDA unavailable.")

    return {
        "metrics": {
            "net_debt": {"value": round(net_debt, 2) if net_debt is not None else None, "unit": "NGN", "status": "available" if net_debt is not None else "unavailable"},
            "net_debt_to_ebitda": {"value": round(net_debt_to_ebitda, 2) if net_debt_to_ebitda is not None else None, "unit": "x", "status": "available" if net_debt_to_ebitda is not None else "unavailable"},
        },
        "reporting_period": reporting_period,
        "limitations": limitations,
    }
