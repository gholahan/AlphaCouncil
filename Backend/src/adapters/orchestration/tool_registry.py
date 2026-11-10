"""Tool Registry - authorized tools per agent role."""

from typing import Any, Dict, List

from src.adapters.mcp.tools.financial_retriever import retrieve_financial_insights
from src.adapters.mcp.tools.ngx_market_tools import (
    fetch_financial_ratios,
    fetch_dividend_history,
    fetch_price_history,
    get_ngx_market_overview,
    fetch_ngx_indices,
)
from src.adapters.mcp.tools.cbn_scraper import get_cbn_fx_rates
from src.adapters.mcp.tools.web_searcher import web_search_financial_context
from src.adapters.mcp.tools.dcf_calculator import run_dcf_model


TOOL_MAP: Dict[str, Any] = {
    "retrieve_financial_insights": retrieve_financial_insights,
    "fetch_financial_ratios": fetch_financial_ratios,
    "fetch_dividend_history": fetch_dividend_history,
    "fetch_price_history": fetch_price_history,
    "get_ngx_market_overview": get_ngx_market_overview,
    "fetch_ngx_indices": fetch_ngx_indices,
    "get_cbn_fx_rates": get_cbn_fx_rates,
    "web_search_financial_context": web_search_financial_context,
    "run_dcf_model": run_dcf_model,
}

_ROLE_TOOLS: Dict[str, List[str]] = {
    "bull_analyst": [
        "retrieve_financial_insights",
        "fetch_financial_ratios",
        "fetch_dividend_history",
        "fetch_price_history",
        "get_ngx_market_overview",
        "fetch_ngx_indices",
        "web_search_financial_context",
    ],
    "bear_analyst": [
        "retrieve_financial_insights",
        "fetch_financial_ratios",
        "fetch_price_history",
        "get_cbn_fx_rates",
        "get_ngx_market_overview",
        "fetch_ngx_indices",
        "web_search_financial_context",
    ],
    "arbitrator": [
        "fetch_financial_ratios",
        "get_cbn_fx_rates",
        "run_dcf_model",
    ],
}


def get_tools_for_role(role: str) -> List[str]:
    return _ROLE_TOOLS.get(role, [])


def get_tools_for_role_objects(role: str) -> List[Any]:
    return [TOOL_MAP[name] for name in _ROLE_TOOLS.get(role, []) if name in TOOL_MAP]


def is_tool_allowed_for_role(role: str, tool_name: str) -> bool:
    return tool_name in _ROLE_TOOLS.get(role, [])
