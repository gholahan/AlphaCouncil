"""Market Data Provider Port - scoped to KoboTerminal NGX API capabilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class StockQuote:
    ticker: str
    price: float
    currency: str = "NGN"
    volume: int = 0
    market_cap: Optional[float] = None
    change_percent: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class FinancialRatios:
    ticker: str
    # Valuation
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    week_52_change: Optional[float] = None
    # Profitability
    roe: Optional[float] = None
    roa: Optional[float] = None
    profit_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    # Leverage
    debt_to_equity: Optional[float] = None
    # Metadata
    as_of_date: Optional[datetime] = None


@dataclass
class DividendRecord:
    ex_dividend_date: Optional[str] = None
    record_date: Optional[str] = None
    pay_date: Optional[str] = None
    dividend_per_share: Optional[float] = None
    currency: str = "NGN"


@dataclass
class OHLCVRecord:
    date: Optional[str] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None


@dataclass
class MarketOverview:
    asi: Optional[float] = None
    asi_change_percent: Optional[float] = None
    market_cap: Optional[float] = None
    volume: Optional[int] = None
    deals: Optional[int] = None
    value: Optional[float] = None
    as_of_date: Optional[datetime] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class MarketDataProvider(ABC):

    @abstractmethod
    async def get_quote(self, ticker: str) -> StockQuote:
        """GET /prices/{ticker} — live price, change%, volume, sector."""
        pass

    @abstractmethod
    async def get_financial_ratios(self, ticker: str) -> FinancialRatios:
        """GET /fundamentals/{ticker} — PE, PB, ROE, margins, EPS, debt/equity."""
        pass

    @abstractmethod
    async def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> List[OHLCVRecord]:
        """GET /history/{ticker} — OHLCV price history."""
        pass

    @abstractmethod
    async def get_dividends(self, ticker: str) -> List[DividendRecord]:
        """GET /dividends/{ticker} — dividend payment history."""
        pass

    @abstractmethod
    async def get_all_stocks(self) -> List[Dict[str, Any]]:
        """GET /stocks — full NGX universe with prices and basic ratios."""
        pass

    @abstractmethod
    async def get_market_overview(self) -> MarketOverview:
        """GET /market — ASI level, market cap, volume, deals."""
        pass

    @abstractmethod
    async def get_market_status(self) -> Dict[str, Any]:
        """GET /market-status — is market open/closed."""
        pass

    @abstractmethod
    async def get_indices(self) -> List[Dict[str, Any]]:
        """GET /indices — ASI, NGX30, NGX Pension index levels."""
        pass

    @abstractmethod
    async def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """GET /prices/{ticker} — name, sector, symbol."""
        pass
