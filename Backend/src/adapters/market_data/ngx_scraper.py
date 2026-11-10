"""NGX market data adapter - NGX Exchange API + African Markets fallback."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import httpx

from src.application.ports.outbound.market_data import MarketDataProvider, StockQuote, FinancialRatios

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "application/json, */*",
}

# NGX Exchange public JSON API
_NGX_API = "https://ngxgroup.com/exchange/data/equities-price-list"
# African Markets NGX data (JSON)
_AFRICAN_MARKETS_API = "https://african-markets.com/api/v1/stock"


class NGXScraperAdapter(MarketDataProvider):
    """
    Market data adapter for Nigerian Exchange (NGX) listed stocks.
    Primary: NGX Exchange public API
    Fallback: African Markets API
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._cache: Dict[str, Dict] = {}

    async def _get_equity_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        ticker = ticker.upper()
        if ticker in self._cache:
            return self._cache[ticker]

        # Primary: NGX Exchange API
        try:
            async with httpx.AsyncClient(headers=_HEADERS, timeout=self.timeout, follow_redirects=True) as client:
                r = await client.get(_NGX_API, params={"symbol": ticker})
                if r.status_code == 200:
                    payload = r.json()
                    # API returns list or dict with data key
                    rows = payload if isinstance(payload, list) else payload.get("data", [])
                    for row in rows:
                        sym = (row.get("symbol") or row.get("ticker") or "").upper()
                        if sym == ticker:
                            result = _normalize(row, ticker)
                            self._cache[ticker] = result
                            return result
        except Exception as e:
            logger.warning(f"[NGX] NGX API failed for {ticker}: {e}")

        # Fallback: African Markets
        try:
            async with httpx.AsyncClient(headers=_HEADERS, timeout=self.timeout, follow_redirects=True) as client:
                r = await client.get(f"{_AFRICAN_MARKETS_API}/{ticker}", params={"exchange": "NGX"})
                if r.status_code == 200:
                    data = r.json()
                    row = data.get("data") or data
                    result = _normalize(row, ticker)
                    self._cache[ticker] = result
                    return result
        except Exception as e:
            logger.warning(f"[NGX] African Markets failed for {ticker}: {e}")

        logger.warning(f"[NGX] No live data found for {ticker} - debate continues with RAG data")
        return None

    async def get_quote(self, ticker: str) -> StockQuote:
        data = await self._get_equity_data(ticker)
        if not data:
            return StockQuote(ticker=ticker, price=0.0, currency="NGN", volume=0)
        return StockQuote(
            ticker=ticker,
            price=data.get("price") or 0.0,
            currency="NGN",
            volume=data.get("volume") or 0,
            market_cap=data.get("market_cap"),
            change_percent=data.get("change_pct"),
            timestamp=datetime.utcnow(),
        )

    async def get_financial_ratios(self, ticker: str) -> FinancialRatios:
        data = await self._get_equity_data(ticker)
        if not data:
            return FinancialRatios(ticker=ticker)
        return FinancialRatios(
            ticker=ticker,
            pe_ratio=data.get("pe_ratio"),
            pb_ratio=data.get("pb_ratio"),
            dividend_yield=data.get("dividend_yield"),
            as_of_date=datetime.utcnow(),
        )

    async def get_historical_prices(
        self, ticker: str, start_date: datetime, end_date: datetime, interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(headers=_HEADERS, timeout=self.timeout, follow_redirects=True) as client:
                r = await client.get(
                    f"{_NGX_API}/history",
                    params={"symbol": ticker, "from": start_date.date().isoformat(), "to": end_date.date().isoformat()},
                )
                if r.status_code == 200:
                    rows = r.json()
                    rows = rows if isinstance(rows, list) else rows.get("data", [])
                    return [
                        {
                            "date": row.get("date"),
                            "open": _f(row.get("open")),
                            "high": _f(row.get("high")),
                            "low": _f(row.get("low")),
                            "close": _f(row.get("close") or row.get("price")),
                            "volume": _i(row.get("volume")),
                        }
                        for row in rows
                    ]
        except Exception as e:
            logger.error(f"[NGX] Historical prices error for {ticker}: {e}")
        return []

    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        data = await self._get_equity_data(ticker)
        return {
            "company_name": data.get("company_name") if data else ticker,
            "ticker": ticker,
            "exchange": "NGX",
            "currency": "NGN",
            "sector": data.get("sector") if data else None,
        }

    async def get_income_statement(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        return {}

    async def get_balance_sheet(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        return {}

    async def get_cash_flow(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        return {}


def _normalize(row: Dict, ticker: str) -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "company_name": row.get("company_name") or row.get("name") or row.get("companyName") or ticker,
        "price": _f(row.get("close") or row.get("price") or row.get("lastPrice") or row.get("last_price") or row.get("closing_price")),
        "change": _f(row.get("change")),
        "change_pct": _f(row.get("changePercent") or row.get("change_pct") or row.get("percentChange") or row.get("percent_change")),
        "volume": _i(row.get("volume") or row.get("deals")),
        "market_cap": _f(row.get("marketCap") or row.get("market_cap")),
        "pe_ratio": _f(row.get("peRatio") or row.get("pe_ratio") or row.get("pe")),
        "pb_ratio": _f(row.get("pbRatio") or row.get("pb_ratio") or row.get("pb")),
        "eps": _f(row.get("eps") or row.get("EPS")),
        "dividend_yield": _f(row.get("dividendYield") or row.get("dividend_yield")),
        "sector": row.get("sector") or row.get("industry"),
    }


def _f(value) -> Optional[float]:
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _i(value) -> Optional[int]:
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, TypeError, AttributeError):
        return None
