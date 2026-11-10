"""KoboTerminal adapter - NGX market data via koboterminal.com API."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.application.ports.outbound.market_data import (
    MarketDataProvider,
    StockQuote,
    FinancialRatios,
    DividendRecord,
    OHLCVRecord,
    MarketOverview,
)
from src.config.settings import settings

logger = logging.getLogger(__name__)

_BASE = "https://koboterminal.com"
_TIMEOUT = 15.0


class KoboTerminalAdapter(MarketDataProvider):

    def __init__(self, api_key: Optional[str] = None, timeout: float = _TIMEOUT):
        self.api_key = api_key or settings.KOBO_API_KEY
        self._client = httpx.AsyncClient(
            base_url=_BASE,
            headers={"X-API-Key": self.api_key or "", "Accept": "application/json"},
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Any]:
        try:
            r = await self._client.get(path, params=params)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.info("[Kobo] %s requires upgraded plan (403 - handled gracefully)", path)
            else:
                logger.error("[Kobo] %s → HTTP %s: %s", path, e.response.status_code, e.response.text[:300])
        except httpx.RequestError:
            logger.exception("[Kobo] request failed: %s", path)
        except ValueError:
            logger.exception("[Kobo] invalid JSON: %s", path)
        return None

    async def get_quote(self, ticker: str) -> StockQuote:
        """Free plan: derive quote from latest session in ?days=7 response."""
        data = await self._get(f"/api/ngxdata/prices/{ticker.upper()}", params={"days": 7})
        if not isinstance(data, dict):
            return StockQuote(ticker=ticker.upper(), price=0.0, volume=0)
        rows = data.get("prices", [])
        latest = rows[-1] if rows else {}
        return StockQuote(
            ticker=data.get("symbol", ticker.upper()),
            price=_f(latest.get("close_price")) or 0.0,
            volume=_i(latest.get("volume")) or 0,
            timestamp=datetime.now(timezone.utc),
        )

    async def get_financial_ratios(self, ticker: str) -> FinancialRatios:
        """Fundamentals endpoint requires Starter plan — returns empty on free tier."""
        data = await self._get(f"/api/ngxdata/fundamentals/{ticker.upper()}")
        fund = data.get("fundamentals") if isinstance(data, dict) else None
        if not isinstance(fund, dict):
            logger.warning("[Kobo] fundamentals unavailable for %s (free plan limit)", ticker)
            return FinancialRatios(ticker=ticker.upper())
        return FinancialRatios(
            ticker=fund.get("symbol", ticker.upper()),
            pe_ratio=_f(fund.get("pe_ratio")),
            pb_ratio=_f(fund.get("pb_ratio")),
            eps=_f(fund.get("eps")),
            dividend_yield=_f(fund.get("dividend_yield")),
            beta=_f(fund.get("beta")),
            week_52_change=_f(fund.get("52w_change")),
            roe=_f(fund.get("roe")),
            roa=_f(fund.get("roa")),
            profit_margin=_f(fund.get("profit_margin")),
            gross_margin=_f(fund.get("gross_margin")),
            debt_to_equity=_f(fund.get("debt_equity")),
            as_of_date=_dt(fund.get("updated_at")),
        )

    async def get_historical_prices(
        self, ticker: str, start_date: datetime, end_date: datetime, interval: str = "1d"
    ) -> List[OHLCVRecord]:
        """Free plan: last 7 sessions only via ?days=7."""
        data = await self._get(
            f"/api/ngxdata/prices/{ticker.upper()}",
            params={"days": 7},
        )
        if not isinstance(data, dict):
            return []
        rows = data.get("prices", [])
        return [
            OHLCVRecord(
                date=row.get("trade_date"),
                open=_f(row.get("open_price")),
                high=_f(row.get("high_price")),
                low=_f(row.get("low_price")),
                close=_f(row.get("close_price")),
                volume=_i(row.get("volume")),
            )
            for row in rows
            if isinstance(row, dict)
        ]

    async def get_dividends(self, ticker: str) -> List[DividendRecord]:
        data = await self._get(f"/api/ngxdata/dividends/{ticker.upper()}")
        if not isinstance(data, dict):
            return []
        rows = data.get("history", [])
        return [
            DividendRecord(
                ex_dividend_date=row.get("ex_dividend_date"),
                record_date=row.get("record_date"),
                pay_date=row.get("pay_date"),
                dividend_per_share=_f(row.get("dividend_per_share")),
                currency=row.get("currency", "NGN"),
            )
            for row in rows
            if isinstance(row, dict)
        ]

    async def get_all_stocks(self) -> List[Dict[str, Any]]:
        data = await self._get("/api/ngxdata/stocks")
        return data if isinstance(data, list) else []

    async def get_market_overview(self) -> MarketOverview:
        data = await self._get("/api/ngxdata/market")
        if not isinstance(data, dict):
            return MarketOverview()
        return MarketOverview(
            asi=_f(data.get("asi") or data.get("index")),
            asi_change_percent=_f(data.get("change_percent") or data.get("asi_change")),
            market_cap=_f(data.get("market_cap")),
            volume=_i(data.get("volume")),
            deals=_i(data.get("deals")),
            value=_f(data.get("value")),
            as_of_date=_dt(data.get("date") or data.get("updated_at")),
            extra={k: v for k, v in data.items() if k not in
                  {"asi", "index", "change_percent", "asi_change", "market_cap", "volume", "deals", "value", "date", "updated_at"}},
        )

    async def get_market_status(self) -> Dict[str, Any]:
        data = await self._get("/api/ngxdata/market-status")
        return data if isinstance(data, dict) else {}

    async def get_indices(self) -> List[Dict[str, Any]]:
        data = await self._get("/api/ngxdata/indices")
        return data if isinstance(data, list) else (list(data.values()) if isinstance(data, dict) else [])

    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        data = await self._get(f"/api/ngxdata/prices/{ticker.upper()}")
        if not isinstance(data, dict):
            return {"ticker": ticker.upper()}
        return {
            "ticker": data.get("symbol", ticker.upper()),
            "company_name": data.get("name", ticker),
            "sector": data.get("sector"),
            "exchange": "NGX",
            "currency": "NGN",
        }


def _f(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _i(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _dt(v) -> Optional[datetime]:
    if not v:
        return None
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
