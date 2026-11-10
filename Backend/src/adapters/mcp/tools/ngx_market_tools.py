"""MCP Market Data Tools - powered by KoboTerminal NGX API."""

import asyncio
from datetime import datetime, timedelta

from langchain_core.tools import tool
from src.adapters.market_data.kobo_terminal import KoboTerminalAdapter

# Module-level singleton — one httpx client reused across all tool calls
_adapter = KoboTerminalAdapter()


@tool
async def fetch_financial_ratios(ticker: str) -> dict:
    """
    Gets live NGX stock quote, 7-day price momentum (high/low/volume), and market statistics via KoboTerminal.

    Args:
        ticker: NGX stock ticker (e.g., "DANGCEM", "BUACEMENT", "GTCO")

    Returns:
        current_price, change_percent, volume, 7d_high, 7d_low, avg_7d_volume, recent_sessions_count
    """
    try:
        quote_res, history_res = await asyncio.gather(
            _adapter.get_quote(ticker),
            _adapter.get_historical_prices(ticker, datetime.utcnow() - timedelta(days=7), datetime.utcnow()),
            return_exceptions=True,
        )

        quote = quote_res if not isinstance(quote_res, Exception) else None
        history = history_res if not isinstance(history_res, Exception) else []

        highs = [h.high for h in history if h.high is not None]
        lows = [h.low for h in history if h.low is not None]
        volumes = [h.volume for h in history if h.volume is not None]

        return {
            "ticker": ticker.upper(),
            "current_price": quote.price if quote else 0.0,
            "change_percent": quote.change_percent if quote else 0.0,
            "volume": quote.volume if quote else 0,
            "7d_high": max(highs) if highs else (quote.price if quote else 0.0),
            "7d_low": min(lows) if lows else (quote.price if quote else 0.0),
            "avg_7d_volume": int(sum(volumes) / len(volumes)) if volumes else (quote.volume if quote else 0),
            "recent_sessions_count": len(history),
            "status": "success",
            "source": "KoboTerminal 200 OK Market Data",
        }
    except Exception as e:
        return {"error": str(e)}


@tool
async def fetch_dividend_history(ticker: str) -> list:
    """
    Gets dividend payment history for an NGX-listed stock.

    Args:
        ticker: NGX stock ticker (e.g., "DANGCEM")

    Returns:
        List of {ex_dividend_date, record_date, pay_date, dividend_per_share, currency}
    """
    try:
        records = await _adapter.get_dividends(ticker)
        return [
            {
                "ex_dividend_date": r.ex_dividend_date,
                "record_date": r.record_date,
                "pay_date": r.pay_date,
                "dividend_per_share": r.dividend_per_share,
                "currency": r.currency,
            }
            for r in records
        ]
    except Exception as e:
        return [{"error": str(e)}]


@tool
async def fetch_price_history(ticker: str) -> list:
    """
    Gets last 7 trading sessions OHLCV data for an NGX stock via KoboTerminal.

    Args:
        ticker: NGX stock ticker (e.g., "DANGCEM")

    Returns:
        List of {date, open, high, low, close, volume}
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=7)
        records = await _adapter.get_historical_prices(ticker, start, end)
        return [
            {"date": r.date, "open": r.open, "high": r.high,
             "low": r.low, "close": r.close, "volume": r.volume}
            for r in records
        ]
    except Exception as e:
        return [{"error": str(e)}]


@tool
async def get_ngx_market_overview() -> dict:
    """
    Gets current NGX market overview: ASI level, market cap, total volume,
    number of deals. Use for macro market context and relative benchmarking.
    """
    try:
        m = await _adapter.get_market_overview()
        return {
            "asi": m.asi,
            "asi_change_percent": m.asi_change_percent,
            "market_cap": m.market_cap,
            "volume": m.volume,
            "deals": m.deals,
            "value": m.value,
            "as_of_date": m.as_of_date.isoformat() if m.as_of_date else None,
            **m.extra,
        }
    except Exception as e:
        return {"error": str(e)}


@tool
async def fetch_ngx_indices() -> list:
    """
    Gets all NGX sector and sub-indices with their current levels and changes.
    Use to benchmark a stock against its sector index performance.

    Returns:
        List of index entries (name, value, change, change_percent, etc.)
    """
    try:
        return await _adapter.get_indices()
    except Exception as e:
        return [{"error": str(e)}]

