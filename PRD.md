# AlphaCouncil: Product Requirements Document

## 1. Executive Summary

### What is AlphaCouncil?

**AlphaCouncil** is an AI-powered investment committee system that uses multi-agent adversarial debate to validate investment theses for Nigerian equity markets (NSE-listed stocks). The system orchestrates five specialized AI agents—each with distinct roles, data sources, and analytical frameworks—to conduct structured debates that stress-test investment decisions through rigorous cross-examination.

### The Core Problem

Investment analysis today suffers from a fundamental asymmetry: **it's easier to find reasons to support a thesis than to challenge it**. When an investor asks a single LLM "Should I buy Dangote Cement?", the model typically responds with a one-sided analysis that either validates or rejects the thesis without adversarial scrutiny. This mirrors how human investors suffer from confirmation bias—they google for articles that support their beliefs, not challenge them.

Traditional solutions are inadequate:
- **Manual research** (reading 10-Ks, analyzing financials, tracking news) takes 4-8 hours per stock
- **Professional analysts** cost ₦50,000-200,000 per report and have their own biases
- **Single-LLM analysis** is fast but shallow, lacks citations, and provides no structured counter-arguments
- **Investment communities** (Twitter, Reddit) are echo chambers where dissenting views get downvoted

### Why Multi-Agent Debate Architecture?

The AlphaCouncil architecture is specifically designed to solve three critical problems that single-agent systems cannot address:

**1. Forced Adversarial Rigor**  
By assigning agents to opposing roles (Bull vs Bear), the system **guarantees** that both sides of the investment case are examined with equal depth. The Fundamental Analyst is incentivized (via prompt engineering) to find supporting evidence, while the Quantitative Auditor is explicitly tasked with finding risks and red flags. This creates a zero-sum debate dynamic where weak arguments get challenged immediately.

**2. Specialization Through Division of Labor**  
Each agent focuses on a narrow analytical domain:
- The **Fundamental Analyst** examines revenue trends, market positioning, and competitive moats
- The **Quantitative Auditor** scrutinizes balance sheet health, debt levels, and accounting quality
- The **Risk & Macro Strategist** contextualizes the investment within broader economic conditions (CBN policy, inflation, currency risk)

This specialization allows each agent to use domain-specific tools and frameworks (e.g., DCF models for valuation, debt covenants analysis for credit risk) without cognitive overload.

**3. Audit Trail & Calibrated Confidence**  
The debate transcript creates a permanent record of what was considered and why. Six months later, when the stock has moved, investors can revisit the original analysis to understand what they got right or wrong. The Arbitrator's confidence score (e.g., 68%) reflects the strength of evidence on both sides—when bull and bear cases are evenly matched, confidence is moderate; when one side dominates, confidence is high.

### Target Users

**Primary:** Retail investors in Nigeria with ₦5M-50M portfolios  
- Typically hold 5-10 stocks (Access Bank, Dangote Cement, MTN Nigeria, etc.)
- Make 2-5 investment decisions per year
- Willing to pay ₦2,000 for rigorous analysis on a ₦5M+ position (0.04% of capital)

**Secondary:** Small fund managers (₦100M-1B AUM)  
- Need documented investment processes for LP reporting
- Require audit trails for compliance
- Value the ability to defensively cite AI-generated analysis ("our investment committee reviewed...")

**Tertiary:** Finance students / investment clubs  
- Use AlphaCouncil as a learning tool to understand multi-dimensional analysis
- Free tier (Tier 1) sufficient for educational use

### Core Value Proposition

**Transform** "Should I buy this stock?" (vague question → vague answer)  
**Into** "Allocate ₦2.5M with stop-loss at ₦365" (specific action → specific recommendation)

**Delivered through:**
- Adversarial AI debate with bull/bear agents
- Evidence-based claims with source citations ([REF:n] links to exact 10-K page)
- Actionable recommendations (allocation size, stop-loss levels, monitoring triggers)
- Full audit trail (save debate transcript, revisit reasoning later)
- Calibrated confidence scores (honest about uncertainty vs. overconfident claims)

---

## 2. The Financial Data Infrastructure Challenge

### Why This is Harder Than It Looks

Building an investment analysis system requires solving a **data acquisition problem** that traditional software engineering doesn't prepare you for. Unlike building a web app where you control the database schema, financial analysis requires stitching together data from:

1. **Regulatory filings** (10-Ks, 10-Qs, 8-Ks) - unstructured 200+ page PDFs
2. **Real-time market data** (stock prices, volumes, market cap)
3. **Derived financial metrics** (P/E ratios, debt-to-equity, interest coverage)
4. **Macro-economic indicators** (CBN policy rates, inflation, FX rates)
5. **News sentiment** (tracking 50+ articles per stock per day)
6. **Historical time series** (5+ years of financial statements for trend analysis)

Each data source has different formats (PDF, JSON, XML, HTML tables), update frequencies (quarterly filings vs real-time prices), and access restrictions (rate limits, API keys, paywalls).

### The Nigerian Market Data Problem

**The specific challenge for AlphaCouncil**: Most free financial APIs (Yahoo Finance, Alpha Vantage, Financial Modeling Prep) have **excellent coverage of US stocks** but **poor coverage of Nigerian stocks (NSE listings)**. For example:

- `yfinance.Ticker("DANGCEM.LG")` might return empty data for Dangote Cement
- SEC EDGAR only has US company filings
- NewsAPI's Nigerian financial news coverage is sparse

This means AlphaCouncil needs a **hybrid data strategy**:
- For **Nigerian stocks**: Build custom scrapers for NSE website, company Investor Relations pages, and Nigerian financial news sites (Punch, Vanguard, BusinessDay)
- For **global context**: Use free APIs for benchmark comparisons (e.g., compare Dangote Cement margins to Holcim, LafargeHolcim)

### The Core Data Pipeline Architecture

```
[Data Sources]                [Ingestion]              [Storage]           [Retrieval]
     ↓                             ↓                       ↓                   ↓
┌─────────────┐              ┌──────────┐          ┌─────────────┐    ┌──────────────┐
│ NSE Website │──scrape────→ │ Scrapers │──JSON──→ │ PostgreSQL  │←───│ Agent Tools  │
│ Company IRs │              └──────────┘          │             │    │              │
└─────────────┘                                     │ - Raw JSON  │    │ retrieve_sec │
                                                    │ - Time-series│   │ fetch_ratios │
┌─────────────┐              ┌──────────┐          │             │    │ get_sentiment│
│ Yahoo Finance│──API call──→ │ Adapters │──JSON──→ │             │    └──────────────┘
│ NewsAPI     │              └──────────┘          └─────────────┘
└─────────────┘                   ↓                       ↓
                             ┌──────────┐          ┌─────────────┐
┌─────────────┐              │  Chunker │          │ pgvector    │
│ 10-K PDFs   │──download──→ │          │──embed─→ │ (embeddings)│
│ Earnings    │              │ 1000-char│          │             │
└─────────────┘              │  chunks  │          │ RAG queries │
                             └──────────┘          └─────────────┘
```

**Key Design Decisions:**

1. **Raw JSON Storage First**: Store API responses and scraped data as-is in PostgreSQL JSONB columns before normalization. This preserves full context and allows schema evolution without migrations.

2. **Dual Storage: Structured + Vector**:
   - **Structured**: Financial ratios, prices, dates in normalized tables for fast queries (`SELECT debt_to_equity FROM financials WHERE ticker='DANGCEM'`)
   - **Vector**: 10-K text chunks in pgvector for semantic search ("What does the 10-K say about cement demand outlook?")

3. **Batch + Real-time Hybrid**:
   - **Batch (daily)**: Scrape 10-Ks, annual reports, quarterly earnings (these update predictably)
   - **Real-time (on-demand)**: Fetch live stock prices, news sentiment when user initiates debate

---

## 3. Complete Data Source Breakdown

### 3.1 SEC-Equivalent Filings (Nigerian Context)

**What We Need**: Annual reports, financial statements, management discussion & analysis (MD&A)

#### Option A: NSE Official Filings (Preferred, Free)
**Source**: Nigerian Exchange Group website  
**URL**: https://ngxgroup.com/  
**Access Method**: Web scraping (no official API as of 2026)

**Implementation**:
```python
import requests
from bs4 import BeautifulSoup
import pdfplumber

def scrape_nse_filings(ticker: str, filing_type: str = "annual_report") -> dict:
    """
    Scrapes NSE website for company filings.
    
    Args:
        ticker: NSE ticker (e.g., 'DANGCEM')
        filing_type: 'annual_report', 'quarterly', 'price_sensitive'
    
    Returns:
        {
            'url': 'https://...',
            'filing_date': '2025-03-15',
            'pdf_path': '/tmp/DANGCEM_AR_2025.pdf',
            'text_extract': '...'  # First 50k characters
        }
    """
    # NSE filing search URL (example structure)
    search_url = f"https://ngxgroup.com/issuers/{ticker}/filings"
    
    response = requests.get(search_url, headers={
        "User-Agent": "AlphaCouncil/1.0 (research@alphacouncil.com)"
    })
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find latest annual report link (XPath varies by NSE site structure)
    filing_links = soup.select('a[href*="annual-report"]')
    
    if not filing_links:
        raise ValueError(f"No {filing_type} found for {ticker}")
    
    latest_filing = filing_links[0]['href']
    pdf_response = requests.get(latest_filing)
    
    # Save PDF locally
    pdf_path = f"/tmp/{ticker}_{filing_type}.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(pdf_response.content)
    
    # Extract text with OCR fallback
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:50]:  # Limit to first 50 pages for speed
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    return {
        'url': latest_filing,
        'filing_date': extract_date_from_filename(latest_filing),
        'pdf_path': pdf_path,
        'text_extract': text[:50000]  # 50k char limit for context
    }
```

**Challenges & Mitigations**:
- **Challenge**: NSE website structure changes break scrapers  
  **Mitigation**: Build a monitoring system that alerts when scraper fails + maintain fallback to company IR pages

- **Challenge**: PDFs are scanned images (no text layer)  
  **Mitigation**: Use Tesseract OCR as fallback: `pip install pytesseract`

#### Option B: Company Investor Relations Pages (Fallback)
**Example**: Dangote Cement IR page  
**URL**: https://www.dangotecement.com/investor-relations/

**Why this is better than NSE scraping**:
- Companies host machine-readable PDFs (not scanned images)
- Includes supplementary materials (earnings call transcripts, investor presentations)
- More reliable URL structure

**Implementation Pattern**:
```python
# Maintain a mapping of tickers → IR URLs
COMPANY_IR_URLS = {
    'DANGCEM': 'https://www.dangotecement.com/investor-relations/financial-results',
    'ACCESSCORP': 'https://www.accessbankplc.com/investor-relations',
    'MTNN': 'https://www.mtnonline.com/investors/'
}

def get_latest_annual_report(ticker: str) -> str:
    ir_url = COMPANY_IR_URLS.get(ticker)
    if not ir_url:
        raise ValueError(f"No IR URL configured for {ticker}")
    
    # Scrape IR page for "2025 Annual Report" link
    # (Implementation similar to NSE scraper above)
```

### 3.2 Real-Time Stock Prices & Financial Ratios

#### Option A: Yahoo Finance (Best Free Option, Partial NSE Coverage)

**Installation**:
```bash
pip install yfinance
```

**Nigerian Stock Tickers on Yahoo Finance**:
- Dangote Cement: `DANGCEM.LG` (`.LG` = Lagos Stock Exchange suffix)
- Access Bank: `ACCESSCORP.LG`
- MTN Nigeria: `MTNN.LG`

**Implementation**:
```python
import yfinance as yf
from typing import Optional

def fetch_financial_ratios(ticker: str) -> dict:
    """
    Fetches financial ratios from Yahoo Finance.
    
    Returns:
        {
            'pe_ratio': 12.5,
            'debt_to_equity': 1.8,
            'current_ratio': 1.2,
            'roe': 0.18,
            'profit_margin': 0.45,
            'revenue_growth': 0.187,  # 18.7% YoY
            'market_cap_ngn': 2100000000000,  # ₦2.1T
            'current_price': 385,
            'data_source': 'yahoo_finance',
            'last_updated': '2026-11-02T07:00:00Z'
        }
    """
    # Try Nigerian ticker first
    stock = yf.Ticker(f"{ticker}.LG")
    info = stock.info
    
    # Fallback to direct ticker if .LG fails
    if not info or info.get('regularMarketPrice') is None:
        stock = yf.Ticker(ticker)
        info = stock.info
    
    # Yahoo Finance returns USD market cap - convert to NGN
    usd_to_ngn = 1450  # Fetch from CBN API in production
    market_cap_usd = info.get('marketCap', 0)
    market_cap_ngn = market_cap_usd * usd_to_ngn if market_cap_usd else None
    
    return {
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'debt_to_equity': info.get('debtToEquity'),
        'current_ratio': info.get('currentRatio'),
        'roe': info.get('returnOnEquity'),
        'profit_margin': info.get('profitMargins'),
        'revenue_growth': info.get('revenueGrowth'),
        'market_cap_ngn': market_cap_ngn,
        'current_price': info.get('regularMarketPrice'),
        'data_source': 'yahoo_finance',
        'last_updated': datetime.utcnow().isoformat()
    }
```

**Limitations**:
- **Coverage**: Only ~30 Nigerian stocks have Yahoo Finance data (top NSE listings)
- **Latency**: 15-minute delay on free tier (acceptable for AlphaCouncil's use case)
- **Missing Data**: Some ratios (interest coverage, asset turnover) not provided

#### Option B: Financial Modeling Prep API (Better Coverage, Rate Limited)

**Free Tier**: 250 API calls/day  
**Sign Up**: https://site.financialmodelingprep.com/developer/docs/

**Why use this over Yahoo Finance**:
- More comprehensive ratio coverage (40+ metrics vs Yahoo's 15)
- Includes DCF valuations, credit ratings, insider trading data
- Historical data goes back 10+ years

**Implementation**:
```python
import requests
from typing import Dict, List

FMP_API_KEY = "your_free_api_key"  # Store in environment variable

def fetch_financial_ratios_fmp(ticker: str) -> Dict:
    """
    Enhanced financial ratios from Financial Modeling Prep.
    Falls back to Yahoo Finance if FMP has no data.
    """
    url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}"
    params = {"apikey": FMP_API_KEY, "limit": 1}  # Latest quarter only
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200 or not response.json():
        # Fallback to Yahoo Finance
        return fetch_financial_ratios(ticker)
    
    data = response.json()[0]  # Most recent quarter
    
    return {
        'pe_ratio': data.get('priceEarningsRatio'),
        'debt_to_equity': data.get('debtEquityRatio'),
        'current_ratio': data.get('currentRatio'),
        'quick_ratio': data.get('quickRatio'),
        'interest_coverage': data.get('interestCoverage'),  # KEY METRIC Yahoo lacks
        'debt_to_assets': data.get('debtToAssets'),
        'asset_turnover': data.get('assetTurnoverRatio'),
        'roe': data.get('returnOnEquity'),
        'roa': data.get('returnOnAssets'),
        'gross_margin': data.get('grossProfitMargin'),
        'operating_margin': data.get('operatingProfitMargin'),
        'net_margin': data.get('netProfitMargin'),
        'data_source': 'financial_modeling_prep',
        'period': data.get('date')
    }
```

**Rate Limit Management**:
```python
import time
from functools import wraps

# Simple rate limiter for free tier (250 calls/day = ~10/hour sustained)
call_timestamps = []

def rate_limit_fmp(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global call_timestamps
        now = time.time()
        
        # Remove timestamps older than 24 hours
        call_timestamps = [ts for ts in call_timestamps if now - ts < 86400]
        
        if len(call_timestamps) >= 250:
            raise Exception("FMP daily rate limit reached (250 calls/day)")
        
        call_timestamps.append(now)
        return func(*args, **kwargs)
    
    return wrapper

@rate_limit_fmp
def fetch_financial_ratios_fmp(ticker: str) -> Dict:
    # ... implementation above
```

### 3.3 News Feeds & Sentiment Analysis

**The Challenge**: Nigerian financial news is fragmented across:
- **Local newspapers**: Punch, Vanguard, BusinessDay, The Guardian Nigeria
- **Business-focused**: Nairametrics, Business Insider Africa
- **Social media**: Nigerian Finance Twitter, Nairaland forums

**No single API provides comprehensive Nigerian stock news coverage**, so we need a **multi-source aggregation strategy**.

#### Source 1: NewsAPI (Free Tier: 100 requests/day)

**Sign Up**: https://newsapi.org/register  
**Coverage**: International news + some Nigerian outlets

**Implementation**:
```python
from newsapi import NewsApiClient
from datetime import datetime, timedelta

NEWS_API_KEY = "your_newsapi_key"
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def get_stock_news(ticker: str, company_name: str, days_back: int = 7) -> List[Dict]:
    """
    Fetches recent news articles mentioning the stock.
    
    Args:
        ticker: 'DANGCEM'
        company_name: 'Dangote Cement' (for better search results)
        days_back: How many days of news to fetch
    
    Returns:
        [
            {
                'title': 'Dangote Cement Reports Q3 Earnings...',
                'description': '...',
                'url': 'https://...',
                'published_at': '2026-10-28T10:30:00Z',
                'source': 'BusinessDay'
            },
            ...
        ]
    """
    # Search query: company name OR ticker
    query = f'"{company_name}" OR {ticker}'
    
    from_date = (datetime.now() - timedelta(days=days_back)).isoformat()
    
    articles = newsapi.get_everything(
        q=query,
        language='en',
        from_param=from_date,
        sort_by='publishedAt',
        page_size=20  # Max results
    )
    
    return articles['articles']
```

#### Source 2: RSS Feeds (No API Key, Unlimited)

**Nigerian Financial News RSS Feeds**:
```python
RSS_FEEDS = {
    'businessday': 'https://businessday.ng/feed/',
    'nairametrics': 'https://nairametrics.com/feed/',
    'punch_business': 'https://punchng.com/topics/business/feed/',
    'vanguard_business': 'https://www.vanguardngr.com/category/business/feed/'
}

import feedparser

def scrape_rss_feeds(ticker: str, company_name: str) -> List[Dict]:
    """
    Scrapes RSS feeds for mentions of company/ticker.
    No rate limits, but articles lack sentiment metadata.
    """
    all_articles = []
    
    for source, feed_url in RSS_FEEDS.items():
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            # Check if company mentioned in title or summary
            text = (entry.title + " " + entry.summary).lower()
            if company_name.lower() in text or ticker.lower() in text:
                all_articles.append({
                    'title': entry.title,
                    'description': entry.summary,
                    'url': entry.link,
                    'published_at': entry.published,
                    'source': source
                })
    
    return all_articles
```

#### Sentiment Analysis (Local Model, Free)

**Why not use LLM for sentiment**? Too slow and expensive to run 50 articles through Claude Haiku for every debate.

**Solution**: Use lightweight sentiment model (runs locally, 100ms per article)

```bash
pip install transformers torch
```

```python
from transformers import pipeline

# Load once at startup (200MB model download)
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",  # Finance-specific BERT model
    device=-1  # CPU (use 0 for GPU)
)

def analyze_sentiment(articles: List[Dict]) -> Dict:
    """
    Runs sentiment analysis on news articles.
    
    Returns:
        {
            'avg_sentiment': 0.72,  # -1 to 1 scale
            'sentiment_label': 'Bullish',  # Bullish/Neutral/Bearish
            'article_scores': [
                {'title': '...', 'score': 0.85, 'label': 'positive'},
                ...
            ],
            'articles_analyzed': 15
        }
    """
    scores = []
    article_scores = []
    
    for article in articles:
        text = article['title'] + " " + (article.get('description') or "")
        
        # FinBERT returns: [{'label': 'positive', 'score': 0.92}]
        result = sentiment_analyzer(text[:512])[0]  # Truncate to model limit
        
        # Convert to -1 to 1 scale
        polarity = result['score'] if result['label'] == 'positive' else -result['score']
        scores.append(polarity)
        
        article_scores.append({
            'title': article['title'],
            'score': polarity,
            'label': result['label']
        })
    
    avg_sentiment = sum(scores) / len(scores) if scores else 0
    
    return {
        'avg_sentiment': round(avg_sentiment, 3),
        'sentiment_label': 'Bullish' if avg_sentiment > 0.2 else 'Bearish' if avg_sentiment < -0.2 else 'Neutral',
        'article_scores': article_scores,
        'articles_analyzed': len(scores)
    }
```

**Performance**: Processes 20 articles in ~2 seconds on CPU (acceptable for on-demand debate execution)

### 3.4 Macro-Economic Indicators (CBN Data)

**What We Need**:
- **Monetary Policy Rate (MPR)**: CBN's benchmark interest rate
- **Inflation Rate**: CPI year-over-year change
- **FX Rates**: Official USD/NGN exchange rate
- **Treasury Bill Yields**: Risk-free rate for WACC calculation

#### Central Bank of Nigeria Data

**Official Source**: https://www.cbn.gov.ng/rates/  
**Problem**: No official API (as of 2026)

**Solution**: Web scraping + caching (data updates monthly, not real-time)

```python
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_cbn_rates() -> Dict:
    """
    Scrapes CBN website for key macro indicators.
    Caches results for 24 hours (these don't update intraday).
    """
    url = "https://www.cbn.gov.ng/rates/MonthlyAvgExchangeRate.asp"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Parse MPR from announcements page
    mpr_url = "https://www.cbn.gov.ng/Out/2026/CCD/MPC-Press-Release.pdf"
    # (In production: parse PDF or scrape announcements page)
    
    return {
        'monetary_policy_rate': 18.75,  # Fetch from latest MPC communique
        'inflation_rate': 21.34,        # From NBS (National Bureau of Statistics)
        'fx_rate_usd_ngn': 1450,        # Official CBN rate
        'treasury_bill_90d': 15.2,      # 90-day T-bill yield
        'last_updated': datetime.utcnow().isoformat(),
        'source': 'central_bank_of_nigeria'
    }
```

**Alternative**: Use **Trading Economics API** (free tier: 1000 calls/month)  
- More reliable than web scraping
- Covers 196 countries including Nigeria
- API: https://tradingeconomics.com/nigeria/indicators

### 3.5 The DCF Valuation Tool (Pure Python, No API)

**Why build this in-house**: DCF models are deterministic math—no need for external APIs or LLMs.

```python
def run_dcf_model(
    free_cash_flow: float,      # Current FCF in millions (NGN)
    growth_rate: float,         # Expected FCF growth rate (e.g., 0.12 = 12%)
    terminal_growth: float,     # Perpetuity growth (usually 0.02-0.03)
    wacc: float,                # Weighted Average Cost of Capital
    shares_outstanding: float,  # Millions of shares
    years: int = 5              # Projection period
) -> Dict:
    """
    Discounted Cash Flow valuation model.
    
    Example usage:
        dcf = run_dcf_model(
            free_cash_flow=180000,      # ₦180B current FCF
            growth_rate=0.12,            # 12% annual growth
            terminal_growth=0.03,        # 3% perpetual growth
            wacc=0.15,                   # 15% discount rate
            shares_outstanding=17000     # 17B shares
        )
        # Returns: {'intrinsic_value_per_share': 420, ...}
    """
    # Year-by-year FCF projections
    projected_fcf = []
    pv_fcf = []
    
    for year in range(1, years + 1):
        fcf = free_cash_flow * ((1 + growth_rate) ** year)
        pv = fcf / ((1 + wacc) ** year)
        projected_fcf.append(fcf)
        pv_fcf.append(pv)
    
    # Terminal value (Gordon Growth Model)
    terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** years)
    
    # Enterprise value = PV of projected FCF + PV of terminal value
    enterprise_value = sum(pv_fcf) + pv_terminal
    
    # Equity value per share
    intrinsic_value_per_share = enterprise_value / shares_outstanding
    
    return {
        'intrinsic_value_per_share': round(intrinsic_value_per_share, 2),
        'enterprise_value_millions': round(enterprise_value, 2),
        'pv_cash_flows': round(sum(pv_fcf), 2),
        'pv_terminal_value': round(pv_terminal, 2),
        'terminal_value': round(terminal_value, 2),
        'projected_fcf': [round(x, 2) for x in projected_fcf],
        'assumptions': {
            'current_fcf': free_cash_flow,
            'growth_rate': growth_rate,
            'terminal_growth': terminal_growth,
            'wacc': wacc,
            'projection_years': years
        },
        'sensitivity_analysis': _run_sensitivity(free_cash_flow, growth_rate, terminal_growth, wacc, shares_outstanding)
    }

def _run_sensitivity(fcf, base_growth, terminal_growth, base_wacc, shares):
    """
    Sensitivity table: What if WACC is 13% instead of 15%?
    What if growth is 10% instead of 12%?
    """
    sensitivity = {}
    
    # WACC sensitivity
    for wacc_adj in [-0.02, 0, 0.02]:  # ±2%
        wacc = base_wacc + wacc_adj
        dcf = run_dcf_model(fcf, base_growth, terminal_growth, wacc, shares, years=5)
        sensitivity[f'wacc_{wacc:.1%}'] = dcf['intrinsic_value_per_share']
    
    # Growth sensitivity
    for growth_adj in [-0.03, 0, 0.03]:  # ±3%
        growth = base_growth + growth_adj
        dcf = run_dcf_model(fcf, growth, terminal_growth, base_wacc, shares, years=5)
        sensitivity[f'growth_{growth:.1%}'] = dcf['intrinsic_value_per_share']
    
    return sensitivity
```

**Why this matters**: The Arbitrator can say *"DCF intrinsic value: ₦420/share at 15% WACC. Sensitivity: If WACC drops to 13%, value rises to ₦485."*

---

## 4. RAG System Architecture: From PDF to Evidence-Based Claims

### The Core Challenge: Making 200-Page PDFs Queryable

When the Fundamental Analyst says *"[REF:1] Revenue grew 18.7% YoY to ₦2.1T in FY2025"*, that claim must be **verifiable**. The [REF:1] citation should link directly to page 42 of Dangote Cement's 10-K filing. This requires:

1. **Document Ingestion**: Download 10-K PDF → Extract text with OCR fallback
2. **Chunking**: Split 200-page document into 500-character chunks with overlap
3. **Embedding**: Convert each chunk to a 1536-dimensional vector
4. **Storage**: Save embeddings in pgvector with metadata (page number, section, ticker)
5. **Retrieval**: When agent asks "What was revenue growth?", find top-5 relevant chunks
6. **Citation**: Return chunk text + metadata → Agent cites as [REF:1] with page number

### Document Ingestion Pipeline

```python
import pdfplumber
from typing import List, Dict
import hashlib

def ingest_10k_filing(pdf_path: str, ticker: str, filing_year: int) -> List[Dict]:
    """
    Extracts text from a 10-K PDF and prepares it for embedding.
    
    Args:
        pdf_path: Local path to downloaded PDF
        ticker: Stock ticker (e.g., 'DANGCEM')
        filing_year: Fiscal year (e.g., 2025)
    
    Returns:
        [
            {
                'text': 'Our revenue for FY2025 was ₦2.1 trillion...',
                'page': 42,
                'section': 'Financial Results',
                'ticker': 'DANGCEM',
                'filing_year': 2025,
                'filing_type': '10-K',
                'chunk_id': 'dangcem_10k_2025_p42_0'
            },
            ...
        ]
    """
    chunks = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            
            if not text:
                # Fallback to OCR for scanned pages
                text = extract_with_ocr(page)
            
            # Detect section (Financial Results, Risk Factors, MD&A, etc.)
            section = detect_section(text, page_num)
            
            # Chunk the page text (explained below)
            page_chunks = chunk_text(text, chunk_size=1000, overlap=200)
            
            for idx, chunk_text in enumerate(page_chunks):
                chunk_id = f"{ticker.lower()}_{filing_year}_p{page_num}_{idx}"
                
                chunks.append({
                    'text': chunk_text,
                    'page': page_num,
                    'section': section,
                    'ticker': ticker,
                    'filing_year': filing_year,
                    'filing_type': '10-K',
                    'chunk_id': chunk_id,
                    'char_count': len(chunk_text)
                })
    
    return chunks

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits text into overlapping chunks for embedding.
    
    Why overlap? A sentence like "Revenue grew 18.7% to ₦2.1T" might
    span chunk boundaries. With 200-char overlap, we preserve context.
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.7:  # Only if we're >70% through chunk
                chunk = chunk[:last_period + 1]
                end = start + last_period + 1
        
        chunks.append(chunk.strip())
        start = end - overlap  # Overlap for context preservation
    
    return chunks

def detect_section(text: str, page_num: int) -> str:
    """
    Heuristic to detect which section of the 10-K we're in.
    This helps agents prioritize certain sections (e.g., "Risk Factors" for Auditor).
    """
    text_lower = text.lower()
    
    # Section headers typically appear in bold/all-caps
    if 'risk factor' in text_lower or 'item 1a' in text_lower:
        return 'Risk Factors'
    elif 'management discussion' in text_lower or 'md&a' in text_lower:
        return 'MD&A'
    elif 'consolidated statement' in text_lower or 'financial statement' in text_lower:
        return 'Financial Statements'
    elif 'note' in text_lower and page_num > 50:  # Notes typically at end
        return 'Notes to Financial Statements'
    else:
        return 'Other'
```

### Embedding Generation

**Why not embed the entire 10-K as one vector?** A 200-page document contains diverse topics (revenue, risks, legal matters, accounting policies). A single embedding would be too dilute—searching for "revenue growth" would match weakly because 95% of the document is irrelevant.

**Solution**: Embed each 1000-character chunk separately.

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model once at startup (runs locally, no API calls)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim embeddings, 40MB model

def generate_embeddings(chunks: List[Dict]) -> List[Dict]:
    """
    Generates embeddings for all chunks in a batch.
    
    Performance: ~1000 chunks/second on CPU (M1 Mac), 5000/second on GPU.
    A 200-page 10-K (~500 chunks) takes ~0.5 seconds to embed.
    """
    texts = [chunk['text'] for chunk in chunks]
    
    # Batch embedding (10x faster than one-by-one)
    embeddings = embedding_model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True
    )
    
    # Attach embedding to each chunk
    for chunk, embedding in zip(chunks, embeddings):
        chunk['embedding'] = embedding.tolist()  # Convert numpy to list for JSON
    
    return chunks
```

**Embedding Model Choice**:
- **all-MiniLM-L6-v2**: 384 dimensions, 40MB, good for general text
- **multi-qa-mpnet-base-cos-v1**: 768 dimensions, 420MB, better for Q&A retrieval
- **OpenAI text-embedding-3-small**: 1536 dimensions, API-based ($0.02 per 1M tokens)

For AlphaCouncil, **multi-qa-mpnet-base-cos-v1** is the best tradeoff:
- **Local inference** (no API costs, no rate limits)
- **Q&A optimized** (trained on question-answer pairs)
- **768 dimensions** (better than 384 for finance jargon)

### Vector Storage with pgvector

```sql
-- PostgreSQL schema with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    chunk_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    filing_year INTEGER NOT NULL,
    filing_type TEXT NOT NULL,  -- '10-K', '10-Q', 'Earnings'
    section TEXT,                -- 'Risk Factors', 'MD&A', etc.
    page INTEGER,
    text TEXT NOT NULL,
    embedding VECTOR(768),       -- 768-dim for multi-qa-mpnet
    char_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast similarity search (HNSW algorithm)
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Index for filtering before vector search
CREATE INDEX ON document_chunks (ticker, filing_year);
```

**Inserting embeddings**:
```python
import psycopg2
from psycopg2.extras import execute_values

def store_chunks_in_db(chunks: List[Dict], conn):
    """
    Stores embedded chunks in PostgreSQL with pgvector.
    """
    cursor = conn.cursor()
    
    # Prepare data for batch insert
    values = [
        (
            chunk['chunk_id'],
            chunk['ticker'],
            chunk['filing_year'],
            chunk['filing_type'],
            chunk['section'],
            chunk['page'],
            chunk['text'],
            chunk['embedding'],  # pgvector handles list[float]
            chunk['char_count']
        )
        for chunk in chunks
    ]
    
    execute_values(
        cursor,
        """
        INSERT INTO document_chunks 
        (chunk_id, ticker, filing_year, filing_type, section, page, text, embedding, char_count)
        VALUES %s
        ON CONFLICT (chunk_id) DO NOTHING
        """,
        values
    )
    
    conn.commit()
```

### Semantic Retrieval: The `retrieve_sec_filings` Tool

```python
from langchain.tools import tool

@tool
def retrieve_sec_filings(ticker: str, query: str, top_k: int = 5) -> str:
    """
    Retrieves relevant excerpts from a company's SEC filings using semantic search.
    
    Args:
        ticker: Stock ticker (e.g., 'DANGCEM')
        query: Natural language question (e.g., "What was revenue growth in FY2025?")
        top_k: Number of relevant chunks to return
    
    Returns:
        Formatted string with citations:
        
        [REF:1] Source: DANGCEM 10-K FY2025, Page 42, Section: MD&A
        "Our revenue for fiscal year 2025 increased by 18.7% year-over-year to ₦2.1 trillion..."
        
        [REF:2] Source: DANGCEM 10-K FY2025, Page 15, Section: Financial Statements
        "Consolidated revenue: ₦2,103,450,000,000 (FY2025) vs ₦1,772,100,000,000 (FY2024)"
    """
    # Generate embedding for the query
    query_embedding = embedding_model.encode([query])[0].tolist()
    
    # Similarity search in pgvector
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            chunk_id,
            ticker,
            filing_year,
            filing_type,
            section,
            page,
            text,
            1 - (embedding <=> %s::vector) AS similarity  -- cosine similarity
        FROM document_chunks
        WHERE ticker = %s
          AND filing_year = (SELECT MAX(filing_year) FROM document_chunks WHERE ticker = %s)
        ORDER BY embedding <=> %s::vector  -- <=> is pgvector's cosine distance operator
        LIMIT %s
        """,
        (query_embedding, ticker, ticker, query_embedding, top_k)
    )
    
    results = cursor.fetchall()
    
    # Format with citations
    formatted = ""
    for idx, row in enumerate(results, start=1):
        chunk_id, ticker, year, filing_type, section, page, text, similarity = row
        
        formatted += f"[REF:{idx}] Source: {ticker} {filing_type} FY{year}, Page {page}, Section: {section}\n"
        formatted += f'"{text}"\n'
        formatted += f"(Relevance: {similarity:.2f})\n\n"
    
    return formatted
```

**How this powers agent claims**:

When Fundamental Analyst's prompt says:
```
Task: Find evidence of revenue growth for {ticker}.
Use the retrieve_sec_filings tool with query "revenue growth year over year".
Cite all claims with [REF:n] markers.
```

The agent calls:
```python
retrieve_sec_filings(ticker="DANGCEM", query="revenue growth year over year")
```

Gets back:
```
[REF:1] Source: DANGCEM 10-K FY2025, Page 42, Section: MD&A
"Our revenue for fiscal year 2025 increased by 18.7% year-over-year to ₦2.1 trillion..."
(Relevance: 0.89)
```

Then outputs:
```
Revenue grew 18.7% YoY to ₦2.1T in FY2025 [REF:1]
```

### Hybrid Search: When Semantic Search Isn't Enough

**Problem**: Semantic search is great for concepts ("What are the main risk factors?") but struggles with exact values:
- Query: "What was the debt-to-equity ratio?"
- Semantic match might return: "We maintain a strong capital structure" (conceptually related but no number)

**Solution**: Combine semantic search with keyword search (PostgreSQL full-text search)

```python
@tool
def retrieve_sec_filings_hybrid(ticker: str, query: str, keywords: List[str] = None, top_k: int = 5) -> str:
    """
    Hybrid retrieval: semantic + keyword search.
    
    Args:
        keywords: Must-have terms (e.g., ['debt', 'equity', 'ratio'])
    """
    query_embedding = embedding_model.encode([query])[0].tolist()
    
    # Build keyword filter
    keyword_filter = ""
    if keywords:
        keyword_conditions = " AND ".join([f"text ILIKE '%{kw}%'" for kw in keywords])
        keyword_filter = f"AND ({keyword_conditions})"
    
    cursor.execute(
        f"""
        SELECT chunk_id, ticker, filing_year, filing_type, section, page, text,
               1 - (embedding <=> %s::vector) AS similarity
        FROM document_chunks
        WHERE ticker = %s
          AND filing_year >= %s  -- Last 3 years
          {keyword_filter}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (query_embedding, ticker, filing_year - 2, query_embedding, top_k)
    )
    
    # ... format results as before
```

**When agents use hybrid**:
- Fundamental Analyst: Semantic only (broad questions like "What drives growth?")
- Quantitative Auditor: Hybrid with keywords `['debt', 'equity', 'leverage']` (needs exact ratios)

### The 3-Agent Core Architecture

AlphaCouncil uses a **streamlined 3-agent system** orchestrated by LangGraph:

```
User Input: {ticker: "DANGCEM", thesis: "Infrastructure boom will drive cement demand"}
       ↓
[Moderator/Orchestrator - LangGraph StateGraph]
       ↓
┌─────────────────────────────────────────────────────┐
│ AGENT 1: The Bull Case Builder (Advocate)          │
│ ────────────────────────────────────────────────   │
│ Persona: Optimistic fundamental analyst             │
│ Tools:                                              │
│  • retrieve_sec_filings (RAG for historical data)   │
│  • fetch_financial_ratios (Yahoo Finance API)       │
│  • web_search_financial_context (Tavily - breaking) │
│                                                     │
│ Output: Bull thesis with [REF:n] + [WEB:n] cites   │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ AGENT 2: The Bear Case Builder (Auditor)           │
│ ────────────────────────────────────────────────   │
│ Persona: Skeptical risk analyst / devil's advocate  │
│ Tools:                                              │
│  • retrieve_sec_filings (debt schedules, risks)     │
│  • fetch_financial_ratios (leverage metrics)        │
│  • web_search_financial_context (negative news)     │
│  • get_cbn_rates (macro headwinds)                  │
│                                                     │
│ Output: Bear thesis, risks with [REF:n] citations  │
└─────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────┐
│ AGENT 3: The Investment Officer (Arbitrator)       │
│ ────────────────────────────────────────────────   │
│ Persona: Chief Investment Officer making final call │
│ Tools:                                              │
│  • run_dcf_model (deterministic valuation)          │
│  • No RAG (reads debate transcript only)            │
│                                                     │
│ Input: Full debate transcript (Agent 1 + Agent 2)  │
│ Output:                                             │
│  • Verdict: BUY/CONDITIONAL_BUY/HOLD/AVOID         │
│  • Position sizing: ₦2.5M (50% of capital)         │
│  • Stop-loss: ₦365 (-5%)                           │
│  • Confidence: 68%                                  │
│  • Monitoring triggers                              │
└─────────────────────────────────────────────────────┘
       ↓
[Save DebateTrace to Supabase PostgreSQL]
       ↓
[Return JSON: {verdict, recommendation, debate_transcript, citations}]
```

**Why 3 Agents Instead of 5?**

The original design in Section 1 showed 5 agents:
1. Fundamental Analyst (Bull)
2. Quantitative Auditor (Bear)
3. Risk & Macro Strategist
4. Moderator
5. Arbitrator

**Simplified to 3**:
1. **Bull Case Builder** - Absorbs Fundamental Analyst + some macro context
2. **Bear Case Builder** - Absorbs Quantitative Auditor + Risk Strategist roles
3. **Investment Officer** - Final arbitrator (Moderator is now just LangGraph routing logic, not an agent)

**Benefits of 3-Agent Design**:
- ⏱️ **Faster**: 3 LLM calls vs 5 (40% time reduction)
- 💰 **Cheaper**: ~$0.03 per debate vs ~$0.05
- 🎯 **Clearer**: Bull vs Bear is intuitive (no confusion about Risk Strategist role)
- 🔧 **Simpler**: Fewer agents = easier to debug and maintain

**When to Use 5-Agent Version**:
- **Tier 3 "Premium Debate"** option (₦5,000 instead of ₦2,000)
- User explicitly requests "deep analysis"
- High-stakes decisions (>₦50M capital deployment)

---

## 5. LangGraph Orchestration: The Debate State Machine

### Why LangGraph Over LangChain Chains?

**LangChain chains** are linear: Agent A → Agent B → Agent C (fixed sequence).

**AlphaCouncil needs conditional flow**:
- If bull and bear cases are evenly matched → Moderator triggers a 4th turn with Risk Strategist
- If Fundamental Analyst provides weak evidence → Moderator asks for deeper analysis
- If no one mentions FX exposure → Moderator explicitly prompts Risk Strategist

**LangGraph** is a state machine framework built on LangChain that supports:
- **Conditional edges**: Route to different agents based on debate state
- **Cycles**: Agents can debate back-and-forth (not just linear)
- **Shared state**: All agents read/write to a shared `DebateState` object

### The Debate State Schema

```python
from typing import TypedDict, List, Annotated
from langgraph.graph import add_messages

class AgentMessage(TypedDict):
    agent_role: str           # 'fundamental_analyst', 'quantitative_auditor', etc.
    content: str              # The agent's argument
    citations: List[str]      # ['REF:1', 'REF:2', ...]
    confidence: float         # 0.0 to 1.0
    timestamp: str

class DebateState(TypedDict):
    # User inputs
    ticker: str
    company_name: str
    user_thesis: str
    capital_to_deploy: float
    risk_tolerance: str       # 'conservative', 'moderate', 'aggressive'
    
    # Debate history (accumulates across turns)
    messages: Annotated[List[AgentMessage], add_messages]
    
    # Current turn metadata
    current_turn: int
    max_turns: int            # Hard cap (default 5)
    
    # Moderator's assessment
    debate_complete: bool     # True → exit to Arbitrator
    bull_strength: float      # 0.0 to 1.0 (Moderator scores bull case)
    bear_strength: float      # 0.0 to 1.0 (Moderator scores bear case)
    
    # Tool call results (cached to avoid redundant API calls)
    financial_ratios: dict
    market_sentiment: dict
    cbn_rates: dict
    dcf_result: dict
    
    # Final output
    final_verdict: dict       # Populated by Arbitrator
```

### The Graph Structure

```python
from langgraph.graph import StateGraph, END

def build_debate_graph():
    """
    Builds the AlphaCouncil debate workflow as a LangGraph state machine.
    """
    workflow = StateGraph(DebateState)
    
    # Node definitions (each is an agent function)
    workflow.add_node("moderator", moderator_node)
    workflow.add_node("fundamental_analyst", fundamental_analyst_node)
    workflow.add_node("quantitative_auditor", quantitative_auditor_node)
    workflow.add_node("risk_strategist", risk_strategist_node)
    workflow.add_node("arbitrator", arbitrator_node)
    
    # Entry point: Moderator decides who speaks first
    workflow.set_entry_point("moderator")
    
    # Conditional edges from Moderator
    workflow.add_conditional_edges(
        "moderator",
        route_from_moderator,  # Function that returns next agent name
        {
            "fundamental_analyst": "fundamental_analyst",
            "quantitative_auditor": "quantitative_auditor",
            "risk_strategist": "risk_strategist",
            "arbitrator": "arbitrator",
            "END": END
        }
    )
    
    # After each agent speaks, return to Moderator
    workflow.add_edge("fundamental_analyst", "moderator")
    workflow.add_edge("quantitative_auditor", "moderator")
    workflow.add_edge("risk_strategist", "moderator")
    
    # Arbitrator is terminal
    workflow.add_edge("arbitrator", END)
    
    return workflow.compile()

def route_from_moderator(state: DebateState) -> str:
    """
    Moderator's routing logic: Who should speak next?
    """
    turn = state['current_turn']
    max_turns = state['max_turns']
    
    # Turn 1: Always start with Fundamental Analyst (bull case)
    if turn == 1:
        return "fundamental_analyst"
    
    # Turn 2: Always Quantitative Auditor (bear case)
    if turn == 2:
        return "quantitative_auditor"
    
    # Turn 3: Risk & Macro Strategist
    if turn == 3:
        return "risk_strategist"
    
    # Turn 4+: Moderator decides if debate needs continuation
    if turn >= max_turns or state['debate_complete']:
        return "arbitrator"
    
    # If bull/bear scores are close (within 0.2), continue debate
    bull = state['bull_strength']
    bear = state['bear_strength']
    
    if abs(bull - bear) < 0.2:
        # Debate is inconclusive, continue
        if turn == 4:
            return "fundamental_analyst"  # Bull gets rebuttal
        else:
            return "quantitative_auditor"  # Bear gets counter-rebuttal
    else:
        # One side is clearly stronger, move to verdict
        return "arbitrator"
```

### Agent Node Implementation

Each agent node:
1. Reads current `DebateState`
2. Calls its LLM with specialized prompt + tools
3. Updates `DebateState` with its message
4. Returns control to Moderator

```python
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

# Tool definitions (already shown above)
tools = [
    retrieve_sec_filings,
    fetch_financial_ratios,
    get_market_sentiment,
    get_cbn_rates,
    run_dcf_model
]

def fundamental_analyst_node(state: DebateState) -> DebateState:
    """
    Fundamental Analyst agent: Builds the bull case.
    """
    # Build agent with specialized prompt
    prompt = f"""
You are a Fundamental Analyst on an investment committee evaluating {state['ticker']}.

Your role: Build the BULL CASE for investing in this stock. Focus on:
- Revenue growth trends
- Margin expansion
- Market positioning and competitive moats
- Industry tailwinds

User's thesis: {state['user_thesis']}

Tools available:
- retrieve_sec_filings: Search 10-K/10-Q for specific information
- fetch_financial_ratios: Get P/E, ROE, margins, etc.
- get_market_sentiment: Analyze recent news sentiment

CRITICAL: Cite ALL claims with [REF:n] markers from tool results.
Do not make unsupported claims.

Previous debate context:
{format_debate_history(state['messages'])}

Your response:
"""
    
    agent = create_react_agent(
        model=ChatGroq(model="llama-3.1-70b-versatile", temperature=0.3),
        tools=tools,
        state_modifier=prompt
    )
    
    # Run agent
    response = agent.invoke({"messages": [("user", prompt)]})
    
    # Extract agent's final answer
    agent_message = response['messages'][-1].content
    
    # Parse citations
    citations = extract_citations(agent_message)  # Regex for [REF:n]
    
    # Update state
    state['messages'].append({
        'agent_role': 'fundamental_analyst',
        'content': agent_message,
        'citations': citations,
        'confidence': estimate_confidence(agent_message),
        'timestamp': datetime.utcnow().isoformat()
    })
    
    state['current_turn'] += 1
    
    return state

def quantitative_auditor_node(state: DebateState) -> DebateState:
    """
    Quantitative Auditor agent: Builds the bear case.
    """
    prompt = f"""
You are a Quantitative Auditor on an investment committee evaluating {state['ticker']}.

Your role: Build the BEAR CASE. Challenge the bull thesis. Focus on:
- Balance sheet risks (high leverage, declining liquidity)
- Deteriorating financial ratios
- Accounting red flags
- Hidden liabilities

Bull case summary:
{state['messages'][-1]['content'] if state['messages'] else 'No bull case yet'}

Tools available:
- retrieve_sec_filings: Search for risk disclosures, debt covenants
- fetch_financial_ratios: Get debt-to-equity, current ratio, interest coverage

CRITICAL: 
1. Cite ALL claims with [REF:n] markers
2. Directly challenge specific bull case claims with counter-evidence
3. Quantify risks (e.g., "If naira depreciates 15%, debt servicing costs rise 25%")

Your response:
"""
    
    agent = create_react_agent(
        model=ChatGroq(model="llama-3.1-70b-versatile", temperature=0.4),  # Slightly higher temp for creativity
        tools=tools,
        state_modifier=prompt
    )
    
    # ... (similar to fundamental_analyst_node)
    
    state['messages'].append({
        'agent_role': 'quantitative_auditor',
        'content': agent_message,
        'citations': citations,
        'confidence': estimate_confidence(agent_message),
        'timestamp': datetime.utcnow().isoformat()
    })
    
    state['current_turn'] += 1
    
    return state
```

### The Moderator's Scoring Logic

```python
def moderator_node(state: DebateState) -> DebateState:
    """
    Moderator: Assesses debate progress and decides next action.
    """
    if state['current_turn'] == 0:
        # Initial routing (no assessment needed)
        return state
    
    # LLM-based scoring of bull vs bear strength
    moderator_prompt = f"""
You are a Moderator overseeing an investment committee debate on {state['ticker']}.

Debate so far:
{format_debate_history(state['messages'])}

Your task:
1. Score the BULL CASE strength (0.0 to 1.0) based on:
   - Quality of evidence (are claims cited?)
   - Specificity of data (exact numbers vs vague claims)
   - Addressing counter-arguments

2. Score the BEAR CASE strength (0.0 to 1.0) on same criteria

3. Decide: Should the debate continue, or is there enough evidence for a verdict?

Respond in JSON:
{{
  "bull_strength": 0.75,
  "bear_strength": 0.65,
  "debate_complete": false,
  "reasoning": "Bull case has strong revenue evidence but hasn't addressed debt concerns raised by Auditor."
}}
"""
    
    moderator_llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.1)
    response = moderator_llm.invoke([("user", moderator_prompt)])
    
    # Parse JSON response
    assessment = json.loads(response.content)
    
    state['bull_strength'] = assessment['bull_strength']
    state['bear_strength'] = assessment['bear_strength']
    state['debate_complete'] = assessment['debate_complete'] or state['current_turn'] >= state['max_turns']
    
    return state
```

### Running the Debate

```python
# Initialize state
initial_state = {
    'ticker': 'DANGCEM',
    'company_name': 'Dangote Cement Plc',
    'user_thesis': 'Dangote Cement will benefit from infrastructure boom',
    'capital_to_deploy': 5000000,  # ₦5M
    'risk_tolerance': 'moderate',
    'messages': [],
    'current_turn': 0,
    'max_turns': 5,
    'debate_complete': False,
    'bull_strength': 0.0,
    'bear_strength': 0.0,
    'financial_ratios': {},
    'market_sentiment': {},
    'cbn_rates': {},
    'dcf_result': {},
    'final_verdict': {}
}

# Build and run graph
graph = build_debate_graph()
final_state = graph.invoke(initial_state)

# Extract final verdict
verdict = final_state['final_verdict']
print(verdict['recommendation_text'])
```

---

## 6. Agent Prompt Engineering: Crafting Distinct Personas

### Why Agent Personas Matter

The quality of AlphaCouncil's debate depends on **agent specialization**. If all agents use generic prompts like "Analyze this stock", they'll produce overlapping, shallow analysis. The system needs:

1. **Role clarity**: Each agent knows its job and stays in character
2. **Opposing incentives**: Bull agent is rewarded for finding positives; Bear agent for finding negatives
3. **Evidence standards**: Agents must cite sources, not hallucinate numbers
4. **Structured output**: Consistent formatting for parsing and citation tracking

### The Fundamental Analyst Prompt (Bull Case)

```python
FUNDAMENTAL_ANALYST_PROMPT = """
# Your Identity
You are a **Fundamental Analyst** on an investment committee evaluating {ticker} ({company_name}).

# Your Role
Build the BULL CASE for investing in this stock. Your goal is to find legitimate reasons 
why this investment could succeed. You are NOT trying to be "balanced"—the Quantitative 
Auditor will provide the bear case. Focus exclusively on strengths and opportunities.

# Your Analysis Framework
1. **Revenue & Growth**: Historical revenue trends, growth drivers, TAM expansion
2. **Profitability**: Margin trends (gross, operating, net), economies of scale
3. **Competitive Position**: Market share, moats, competitive advantages
4. **Industry Tailwinds**: Macro trends that benefit this company
5. **Management Quality**: Track record, capital allocation, strategic vision

# User's Investment Thesis
{user_thesis}

# Previous Debate Context
{format_debate_history(state['messages'])}

# Your Task
1. Use the `retrieve_sec_filings` tool to find evidence in 10-K/10-Q filings
   - Query for: revenue growth, margin expansion, market share gains, industry outlook
   
2. Use the `fetch_financial_ratios` tool to get current metrics
   - Look for: strong ROE (>15%), healthy margins, revenue growth
   
3. Use the `get_market_sentiment` tool to gauge investor/analyst sentiment
   - Positive news coverage supports the bull case

# Critical Requirements
- **CITE EVERY CLAIM**: Use [REF:n] markers from tool results
  ✓ Good: "Revenue grew 18.7% YoY to ₦2.1T [REF:1]"
  ✗ Bad: "Revenue is growing strongly" (no citation)

- **BE SPECIFIC**: Use exact numbers, not vague terms
  ✓ Good: "Gross margin improved from 42.3% to 45.1%"
  ✗ Bad: "Margins are improving"

- **ACKNOWLEDGE LIMITATIONS**: If you can't find strong evidence, say so
  ✓ Good: "10-K does not disclose market share data [REF:2]"
  ✗ Bad: Making up a market share number

- **FORMAT YOUR RESPONSE**:
```
## Bull Case Summary
[One-paragraph overview of why this is a good investment]

## Key Strengths

### 1. Revenue Growth
[Evidence with [REF:n] citations]

### 2. Margin Expansion
[Evidence with [REF:n] citations]

### 3. Competitive Moats
[Evidence with [REF:n] citations]

## Catalysts
[Upcoming events/trends that could drive price higher]

## Confidence Assessment
[How strong is this bull case? What evidence is missing?]
```

# Example of Good Output
```
## Bull Case Summary
Dangote Cement is well-positioned to benefit from Nigeria's infrastructure boom, 
with strong revenue growth (18.7% YoY [REF:1]) and margin expansion (gross margin 
up to 45.1% [REF:2]). The company dominates the Nigerian cement market with an 
estimated 65% market share [REF:3].

## Key Strengths

### 1. Revenue Growth Momentum
Revenue grew from ₦1.77T (FY2024) to ₦2.10T (FY2025), representing 18.7% YoY 
growth [REF:1]. This outpaced the cement industry's 12% growth rate [REF:4], 
indicating market share gains.

### 2. Margin Expansion Despite Input Cost Inflation
Gross margin improved from 42.3% to 45.1% [REF:2], driven by operational efficiency 
and pricing power. EBITDA margin reached 38.2%, best-in-class for the industry [REF:5].

[... continue]
```

Now, analyze {ticker} and build the bull case.
"""
```

**Key Design Choices**:

1. **"You are NOT trying to be balanced"**: Explicitly tells the agent to be one-sided. Without this, LLMs default to presenting both sides, which defeats the debate structure.

2. **Specific query suggestions**: "Query for: revenue growth, margin expansion..." guides the agent to make useful tool calls instead of vague queries.

3. **Good/Bad examples**: LLMs respond well to concrete examples of desired vs undesired output.

4. **Structured format**: The markdown template ensures consistent, parseable output.

### The Quantitative Auditor Prompt (Bear Case)

```python
QUANTITATIVE_AUDITOR_PROMPT = """
# Your Identity
You are a **Quantitative Auditor** on an investment committee evaluating {ticker} ({company_name}).

# Your Role
Build the BEAR CASE. Your job is to find risks, red flags, and reasons this investment 
could fail. You are the "devil's advocate"—challenge the bull thesis aggressively.

# Your Analysis Framework
1. **Balance Sheet Risk**: High leverage, declining liquidity, off-balance-sheet liabilities
2. **Cash Flow Quality**: FCF vs reported earnings, working capital trends, capex needs
3. **Deteriorating Metrics**: Declining ROE, margin compression, rising debt ratios
4. **Accounting Red Flags**: Revenue recognition changes, one-time gains, goodwill impairments
5. **Hidden Liabilities**: Pension obligations, legal contingencies, FX exposure

# Bull Case You're Challenging
{state['messages'][-1]['content'] if state['messages'] else 'No bull case yet'}

# Your Task
1. **Directly challenge bull claims**: If the Fundamental Analyst cited revenue growth, 
   look for quality issues (e.g., growth funded by debt, working capital deterioration)

2. Use `retrieve_sec_filings` to search for:
   - Risk factors section
   - Debt covenants and maturities
   - Management's discussion of challenges
   - Related party transactions

3. Use `fetch_financial_ratios` to find:
   - Debt-to-equity > 1.5 (high leverage)
   - Current ratio < 1.0 (liquidity crunch)
   - Interest coverage < 3.0x (debt servicing risk)
   - Declining ROE trend

# Critical Requirements
- **QUANTIFY RISKS**: Don't say "high debt"—say "Debt-to-equity: 1.8 vs industry avg 1.2 [REF:4]"
- **CITE COUNTER-EVIDENCE**: Every risk must be sourced from filings or financial data
- **USE SCENARIO ANALYSIS**: "If naira depreciates 15%, debt servicing costs rise 25%"

# Response Format
```
## Bear Case Summary
[One-paragraph overview of key risks]

## Critical Risks

### 1. Balance Sheet Leverage
[Specific debt levels, covenants, interest coverage with [REF:n]]

### 2. [Second major risk]
[Evidence]

### 3. [Third major risk]
[Evidence]

## Bull Case Rebuttals
[Address specific claims from Fundamental Analyst]

## Downside Scenarios
[What could go wrong? Quantify potential losses]

## Confidence Assessment
[How severe are these risks? Any mitigating factors?]
```

Now, build the bear case for {ticker} and challenge the bull thesis.
"""
```

**Adversarial Design Elements**:

1. **"Challenge the bull thesis aggressively"**: Sets an adversarial tone
2. **"Directly challenge bull claims"**: Forces engagement with prior arguments, not just independent analysis
3. **Scenario analysis requirement**: "If naira depreciates 15%..." makes risks concrete

### The Risk & Macro Strategist Prompt

```python
RISK_MACRO_STRATEGIST_PROMPT = """
# Your Identity
You are a **Risk & Macro Strategist** on an investment committee evaluating {ticker} ({company_name}).

# Your Role
Contextualize this investment within the broader macro-economic environment. Your focus:
1. **Monetary Policy**: How do CBN rates affect this company's cost of capital?
2. **Inflation**: Does high inflation help (pricing power) or hurt (input costs)?
3. **Currency Risk**: FX exposure to USD-denominated debt/revenue
4. **Sector-Specific Macro**: Infrastructure spending, oil prices, regulatory changes

# Previous Debate
**Bull Case**: {get_agent_message(state, 'fundamental_analyst')}
**Bear Case**: {get_agent_message(state, 'quantitative_auditor')}

# Your Task
1. Use `get_cbn_rates` to fetch current MPR, inflation, FX rates

2. Use `run_dcf_model` to calculate intrinsic value:
   - Extract FCF from financial ratios
   - Estimate growth rate from historical trends
   - Use CBN rates to calculate WACC (risk-free rate + equity risk premium)
   - Compare DCF intrinsic value to current market price

3. Assess macro risks:
   - What if CBN raises rates by another 200 bps?
   - What if naira depreciates 20% (historical volatility)?
   - What if infrastructure spending bill gets delayed?

# Critical Requirements
- **QUANTIFY MACRO IMPACT**: "15% naira depreciation → +25% debt servicing costs [REF:6]"
- **PROVIDE VALUATION ANCHOR**: DCF intrinsic value gives objective price target
- **STRESS TEST**: Best case / base case / worst case scenarios

# Response Format
```
## Macro Context
[Current CBN policy, inflation, FX environment]

## Valuation Analysis
### DCF Model Results
- Intrinsic value: ₦420/share
- Current price: ₦385/share
- Margin of safety: 9%
- Key assumptions: [list]

### Sensitivity Analysis
[How does value change with different WACC/growth assumptions?]

## Macro Risk Factors
### 1. Monetary Policy Risk
[CBN rate trajectory, impact on WACC]

### 2. Currency Risk
[FX exposure quantified]

### 3. [Other macro risks]

## Investment Outlook
[Given macro backdrop, is this a good risk/reward?]
```

Now, provide the macro context for {ticker}.
"""
```

**Macro-Specific Elements**:

1. **Mandatory DCF calculation**: Ensures an objective valuation anchor (not just sentiment)
2. **Stress testing**: "What if X happens?" forces probabilistic thinking
3. **Integration with prior arguments**: References bull/bear cases to synthesize

### The Moderator Prompt (Meta-Reasoning)

```python
MODERATOR_PROMPT = """
# Your Identity
You are the **Moderator** of an investment committee debate on {ticker}.

# Your Role
Assess the quality and completeness of the debate. Decide:
1. Is there enough evidence to reach a verdict?
2. Are there critical gaps in analysis?
3. Should the debate continue, or move to the Arbitrator?

# Debate History
{format_full_debate(state['messages'])}

# Scoring Criteria

## Bull Case Strength (0.0 to 1.0)
- **1.0**: Multiple strong, cited data points; addresses risks; specific catalysts
- **0.7**: Good evidence but missing key metrics (e.g., no market share data)
- **0.5**: Vague claims or weak citations
- **0.3**: Mostly unsupported assertions

## Bear Case Strength (0.0 to 1.0)
- **1.0**: Quantified risks with scenario analysis; directly rebuts bull claims
- **0.7**: Solid risk identification but lacks quantification
- **0.5**: Generic risks without company-specific evidence
- **0.3**: No engagement with bull case

# Decision Logic
- If |bull_strength - bear_strength| < 0.2 AND turn < max_turns:
  → Continue debate (agents need to provide more evidence)
  
- If both bull_strength > 0.7 AND bear_strength > 0.7:
  → Move to Arbitrator (high-quality arguments on both sides)
  
- If turn >= max_turns:
  → Move to Arbitrator (prevent infinite loops)

# Response Format (JSON only)
```json
{
  "bull_strength": 0.75,
  "bear_strength": 0.65,
  "debate_complete": false,
  "next_speaker": "fundamental_analyst",  // or "arbitrator" if complete
  "reasoning": "Bull case has strong revenue evidence [REF:1,2] but hasn't addressed 
                the debt concerns [REF:4,5] raised by Auditor. One more turn for 
                Fundamental Analyst to respond to leverage concerns."
}
```

Assess the current debate state.
"""
```

**Moderator's Key Functions**:

1. **Quality gating**: Prevents moving to verdict when evidence is weak
2. **Gap identification**: "Bull case hasn't addressed debt concerns"
3. **Dynamic routing**: Can send debate back to specific agent for rebuttal

### The Arbitrator Prompt (Final Synthesis)

```python
ARBITRATOR_PROMPT = """
# Your Identity
You are the **Chief Investment Officer** making the final investment decision on {ticker}.

# Your Mandate
Synthesize the debate into an actionable recommendation. You must:
1. Weigh bull vs bear arguments by evidence quality, not quantity
2. Produce a specific allocation recommendation (not vague "consider buying")
3. Define risk controls (stop-loss, position sizing, monitoring triggers)
4. Calibrate confidence honestly (65% confidence ≠ 95% confidence)

# Complete Debate Transcript
{format_full_debate(state['messages'])}

# User Context
- Capital to deploy: ₦{state['capital_to_deploy']:,.0f}
- Risk tolerance: {state['risk_tolerance']}
- User's original thesis: {state['user_thesis']}

# Your Decision Framework

## Verdict Options
1. **STRONG BUY**: Allocate 100% of capital; high conviction (>80% confidence)
2. **BUY**: Allocate 60-80% of capital; solid case, manageable risks
3. **CONDITIONAL BUY**: Allocate 30-50% with strict stop-loss; balanced risk/reward
4. **HOLD**: Do not invest; insufficient margin of safety
5. **AVOID**: Material risks outweigh potential upside

## Risk Controls Matrix
| Risk Tolerance | Stop-Loss | Position Size | Monitoring Frequency |
|----------------|-----------|---------------|----------------------|
| Conservative   | -3%       | 20-40%        | Daily                |
| Moderate       | -5%       | 40-60%        | Weekly               |
| Aggressive     | -8%       | 60-100%       | Monthly              |

## Confidence Calibration
- **85-95%**: Overwhelming evidence on one side; limited downside scenarios
- **70-85%**: Strong case with acknowledged risks; good margin of safety
- **55-70%**: Balanced arguments; thin margin of safety (use CONDITIONAL BUY)
- **40-55%**: Weak bull case or severe bear case; recommend HOLD/AVOID
- **<40%**: Insufficient evidence to make any recommendation

# Response Format (JSON)
```json
{
  "verdict": "CONDITIONAL_BUY",
  "verdict_label": "Conditional Buy",
  "confidence": 0.68,
  
  "recommendation": {
    "allocation_ngn": 2500000,
    "allocation_percentage": 0.50,
    "rationale": "Fundamentals support growth thesis (18.7% revenue growth [REF:1], 
                  margin expansion [REF:2]), but elevated leverage (D/E: 1.8 [REF:4]) 
                  and FX exposure [REF:6] warrant caution. Thin 9% margin of safety 
                  from DCF [REF:8] justifies reduced position size.",
    
    "stop_loss_ngn": 365,
    "stop_loss_percentage": -0.05,
    
    "target_price_ngn": 420,
    "time_horizon_months": 12
  },
  
  "bull_case_summary": "Strong revenue growth, margin expansion, market leadership",
  "bear_case_summary": "High leverage, FX exposure, thin valuation margin",
  
  "key_risks": [
    {
      "risk": "Debt-to-equity ratio: 1.8 (industry avg: 1.2)",
      "severity": "HIGH",
      "mitigation": "Monitor quarterly debt servicing costs; exit if D/E exceeds 2.0"
    },
    {
      "risk": "40% USD-denominated debt; 15% naira depreciation → +25% servicing costs",
      "severity": "HIGH",
      "mitigation": "Monitor USD/NGN rate weekly; reassess if rate exceeds ₦1,600/$"
    },
    {
      "risk": "Thin 9% margin of safety from DCF intrinsic value",
      "severity": "MEDIUM",
      "mitigation": "Limit position size to 50% of intended capital"
    }
  ],
  
  "monitoring_triggers": [
    "Debt-to-equity drops below 1.5 → Consider increasing allocation to 75%",
    "Interest coverage falls below 2.5x → Immediate reassessment",
    "Quarterly revenue growth < 10% for 2 consecutive quarters → Review thesis",
    "Naira depreciates beyond ₦1,600/$ → Reduce position or exit",
    "Stop-loss triggered at ₦365 → Exit position immediately"
  ],
  
  "alternative_scenarios": {
    "bull_scenario": "If infrastructure bill passes and debt refinanced at lower rates, 
                      intrinsic value could rise to ₦485/share → 26% upside",
    "bear_scenario": "If FX crisis occurs (naira to ₦1,800/$) and cement demand weakens, 
                      downside to ₦320/share → -17% loss (stopped at -5%)"
  },
  
  "investment_memo_summary": "CONDITIONAL BUY on Dangote Cement at ₦385/share. Allocate 
                              ₦2.5M (50% of capital) with strict ₦365 stop-loss. Strong 
                              fundamentals offset by balance sheet risks and thin valuation 
                              margin. Monitor debt levels and FX exposure closely. 
                              Confidence: 68% (Moderate conviction)."
}
```

Make your final investment decision.
"""
```

**Arbitrator's Unique Requirements**:

1. **Strict JSON output**: Enables programmatic parsing for UI display
2. **Risk-adjusted position sizing**: Conservative risk → smaller position + tighter stop-loss
3. **Monitoring triggers**: Not just "monitor debt"—specific thresholds that trigger action
4. **Alternative scenarios**: Forces probabilistic thinking (bull case, bear case, base case)

---

## 7. Complete Tool Ecosystem & Implementation

### Tool Binding Pattern (LangChain Tools)

All tools follow this pattern:

```python
from langchain.tools import tool
from typing import Dict, List, Optional
import json

@tool
def tool_name(param1: str, param2: int) -> str:
    """
    Tool description that the LLM sees when deciding whether to use this tool.
    Be specific about what the tool does and when to use it.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
    
    Returns:
        JSON string with results (agents parse this)
    """
    try:
        # Tool implementation
        result = do_the_work(param1, param2)
        
        # Return JSON for easy parsing
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Return error as JSON (agent can handle gracefully)
        return json.dumps({
            "error": str(e),
            "tool": "tool_name",
            "params": {"param1": param1, "param2": param2}
        })
```

### Tool 1: `retrieve_sec_filings` (Already Detailed Above)

**Purpose**: Semantic search over 10-K/10-Q documents  
**Used by**: All agents (different queries per agent)  
**Implementation**: Shown in Section 4 (RAG System Architecture)

### Tool 2: `fetch_financial_ratios` (Complete Implementation)

```python
@tool
def fetch_financial_ratios(ticker: str) -> str:
    """
    Fetches comprehensive financial ratios for a stock.
    Tries multiple data sources (Yahoo Finance, Financial Modeling Prep) with fallbacks.
    
    Args:
        ticker: Stock ticker (e.g., 'DANGCEM' or 'DANGCEM.LG' for Nigerian stocks)
    
    Returns:
        JSON with 20+ financial metrics, data source, and last update time
    """
    import yfinance as yf
    import requests
    from datetime import datetime
    
    results = {
        "ticker": ticker,
        "data_source": None,
        "last_updated": datetime.utcnow().isoformat(),
        "ratios": {},
        "warnings": []
    }
    
    # Try Yahoo Finance first (free, unlimited)
    try:
        stock = yf.Ticker(f"{ticker}.LG")  # Nigerian stocks use .LG suffix
        info = stock.info
        
        if info and info.get('regularMarketPrice'):
            results["data_source"] = "yahoo_finance"
            results["ratios"] = {
                "current_price": info.get('regularMarketPrice'),
                "market_cap_usd": info.get('marketCap'),
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "peg_ratio": info.get('pegRatio'),
                "price_to_book": info.get('priceToBook'),
                "price_to_sales": info.get('priceToSalesTrailing12Months'),
                "debt_to_equity": info.get('debtToEquity'),
                "current_ratio": info.get('currentRatio'),
                "quick_ratio": info.get('quickRatio'),
                "return_on_equity": info.get('returnOnEquity'),
                "return_on_assets": info.get('returnOnAssets'),
                "profit_margin": info.get('profitMargins'),
                "operating_margin": info.get('operatingMargins'),
                "revenue_growth_yoy": info.get('revenueGrowth'),
                "earnings_growth_yoy": info.get('earningsGrowth'),
                "beta": info.get('beta'),
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow')
            }
            
            # Remove None values
            results["ratios"] = {k: v for k, v in results["ratios"].items() if v is not None}
            
            return json.dumps(results, indent=2)
    
    except Exception as e:
        results["warnings"].append(f"Yahoo Finance failed: {str(e)}")
    
    # Fallback to Financial Modeling Prep
    try:
        FMP_API_KEY = os.getenv("FMP_API_KEY")
        if not FMP_API_KEY:
            raise ValueError("FMP_API_KEY environment variable not set")
        
        url = f"https://financialmodelingprep.com/api/v3/ratios/{ticker}"
        response = requests.get(url, params={"apikey": FMP_API_KEY, "limit": 1})
        response.raise_for_status()
        
        data = response.json()[0]  # Latest quarter
        
        results["data_source"] = "financial_modeling_prep"
        results["ratios"] = {
            "period": data.get('date'),
            "current_ratio": data.get('currentRatio'),
            "quick_ratio": data.get('quickRatio'),
            "cash_ratio": data.get('cashRatio'),
            "debt_to_equity": data.get('debtEquityRatio'),
            "debt_to_assets": data.get('debtToAssets'),
            "interest_coverage": data.get('interestCoverage'),  # Key metric Yahoo lacks
            "asset_turnover": data.get('assetTurnoverRatio'),
            "inventory_turnover": data.get('inventoryTurnover'),
            "return_on_equity": data.get('returnOnEquity'),
            "return_on_assets": data.get('returnOnAssets'),
            "return_on_capital_employed": data.get('returnOnCapitalEmployed'),
            "gross_profit_margin": data.get('grossProfitMargin'),
            "operating_profit_margin": data.get('operatingProfitMargin'),
            "net_profit_margin": data.get('netProfitMargin'),
            "ebitda_margin": data.get('ebitda'),
            "dividend_yield": data.get('dividendYield'),
            "payout_ratio": data.get('payoutRatio')
        }
        
        results["ratios"] = {k: v for k, v in results["ratios"].items() if v is not None}
        
        return json.dumps(results, indent=2)
    
    except Exception as e:
        results["warnings"].append(f"Financial Modeling Prep failed: {str(e)}")
    
    # If both sources fail
    if not results["ratios"]:
        results["error"] = "All data sources failed. Stock may not be covered by these providers."
    
    return json.dumps(results, indent=2)
```

### Tool 3: `get_market_sentiment` (News + Sentiment Analysis)

```python
@tool
def get_market_sentiment(ticker: str, company_name: str, days_back: int = 7) -> str:
    """
    Analyzes recent news sentiment for a stock using Nigerian news sources.
    
    Args:
        ticker: Stock ticker (e.g., 'DANGCEM')
        company_name: Full company name (e.g., 'Dangote Cement') for better search
        days_back: Number of days of news to analyze (default 7)
    
    Returns:
        JSON with sentiment score (-1 to 1), sentiment label, and article list
    """
    from newsapi import NewsApiClient
    from transformers import pipeline
    import feedparser
    from datetime import datetime, timedelta
    
    # Initialize sentiment analyzer (cached globally to avoid reloading)
    global sentiment_analyzer
    if 'sentiment_analyzer' not in globals():
        sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            device=-1  # CPU
        )
    
    articles = []
    
    # Source 1: NewsAPI
    try:
        newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        from_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        response = newsapi.get_everything(
            q=f'"{company_name}" OR {ticker}',
            language='en',
            from_param=from_date,
            sort_by='publishedAt',
            page_size=20
        )
        
        articles.extend(response['articles'])
    
    except Exception as e:
        pass  # Silently fallback to RSS if NewsAPI fails
    
    # Source 2: Nigerian RSS Feeds
    RSS_FEEDS = {
        'businessday': 'https://businessday.ng/feed/',
        'nairametrics': 'https://nairametrics.com/feed/',
        'punch': 'https://punchng.com/topics/business/feed/'
    }
    
    for source, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:  # Limit per feed
                text = (entry.title + " " + entry.summary).lower()
                if company_name.lower() in text or ticker.lower() in text:
                    articles.append({
                        'title': entry.title,
                        'description': entry.summary,
                        'url': entry.link,
                        'publishedAt': entry.published,
                        'source': {'name': source}
                    })
        except:
            continue
    
    if not articles:
        return json.dumps({
            "error": f"No news articles found for {ticker} in last {days_back} days",
            "avg_sentiment": 0.0,
            "sentiment_label": "No Data"
        })
    
    # Run sentiment analysis
    article_scores = []
    for article in articles:
        text = article.get('title', '') + " " + (article.get('description') or '')
        text = text[:512]  # FinBERT max length
        
        try:
            result = sentiment_analyzer(text)[0]
            polarity = result['score'] if result['label'] == 'positive' else -result['score']
            
            article_scores.append({
                'title': article['title'],
                'url': article.get('url'),
                'sentiment_score': round(polarity, 3),
                'sentiment_label': result['label'],
                'published_at': article.get('publishedAt'),
                'source': article.get('source', {}).get('name')
            })
        
        except:
            continue  # Skip articles that fail sentiment analysis
    
    # Calculate average sentiment
    sentiments = [a['sentiment_score'] for a in article_scores]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    
    # Determine label
    if avg_sentiment > 0.2:
        label = "Bullish"
    elif avg_sentiment < -0.2:
        label = "Bearish"
    else:
        label = "Neutral"
    
    return json.dumps({
        "ticker": ticker,
        "company_name": company_name,
        "avg_sentiment": round(avg_sentiment, 3),
        "sentiment_label": label,
        "articles_analyzed": len(article_scores),
        "date_range": f"Last {days_back} days",
        "top_articles": article_scores[:5],  # Top 5 for brevity
        "all_articles": article_scores  # Full list for agent reference
    }, indent=2)
```

### Tool 4: `get_cbn_rates` (Macro Data)

```python
@tool
def get_cbn_rates() -> str:
    """
    Fetches current Central Bank of Nigeria monetary policy rates and macro indicators.
    Scrapes CBN website as no official API exists. Results cached for 24 hours.
    
    Returns:
        JSON with MPR, inflation rate, FX rate, T-bill yields
    """
    import requests
    from bs4 import BeautifulSoup
    import redis
    from datetime import datetime, timedelta
    
    # Check cache first (avoid hitting CBN website on every debate)
    cache_key = "cbn_rates"
    cache = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data  # Return cached JSON
    
    # Scrape CBN website
    rates = {
        "monetary_policy_rate": None,
        "inflation_rate": None,
        "fx_rate_usd_ngn": None,
        "treasury_bill_90d": None,
        "treasury_bill_180d": None,
        "last_mpc_meeting": None,
        "data_source": "central_bank_of_nigeria",
        "last_updated": datetime.utcnow().isoformat()
    }
    
    try:
        # MPR from MPC communique page
        mpc_url = "https://www.cbn.gov.ng/monetarypolicy/default.asp"
        response = requests.get(mpc_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse MPR (structure varies, use regex as fallback)
        import re
        mpr_match = re.search(r'MPR.*?(\d+\.\d+)%', response.text, re.IGNORECASE)
        if mpr_match:
            rates["monetary_policy_rate"] = float(mpr_match.group(1))
        
        # FX rate from CBN rates page
        fx_url = "https://www.cbn.gov.ng/rates/ExchRateByCurrency.asp"
        fx_response = requests.get(fx_url, timeout=10)
        fx_soup = BeautifulSoup(fx_response.text, 'html.parser')
        
        # Find USD row in table (parsing logic depends on CBN site structure)
        # This is a simplified example
        usd_rate_match = re.search(r'USD.*?(\d+\.\d+)', fx_response.text)
        if usd_rate_match:
            rates["fx_rate_usd_ngn"] = float(usd_rate_match.group(1))
        
        # T-bill yields from auction results
        tbill_url = "https://www.cbn.gov.ng/securitys/treasury.asp"
        tbill_response = requests.get(tbill_url, timeout=10)
        
        # Parse 90-day T-bill yield (example)
        tbill_90_match = re.search(r'90.*?(\d+\.\d+)%', tbill_response.text)
        if tbill_90_match:
            rates["treasury_bill_90d"] = float(tbill_90_match.group(1))
    
    except Exception as e:
        # If scraping fails, return manual fallback values (update these periodically)
        rates.update({
            "monetary_policy_rate": 18.75,  # As of Nov 2026 (example)
            "inflation_rate": 21.34,
            "fx_rate_usd_ngn": 1450,
            "treasury_bill_90d": 15.2,
            "warning": f"Live scraping failed: {str(e)}. Using fallback values as of 2026-11-01."
        })
    
    result = json.dumps(rates, indent=2)
    
    # Cache for 24 hours
    cache.setex(cache_key, timedelta(hours=24), result)
    
    return result
```

### Tool 5: `run_dcf_model` (Valuation Calculator)

**(Already detailed in Section 3.5 above)**

### Tool 6: `web_search_financial_context` (Live Market Intelligence)

**Why Add Web Search?**

RAG (embedded documents) provides deep historical analysis, but it's **static**. A 10-K from 6 months ago doesn't tell you:
- "Dangote Cement raised prices 15% yesterday due to diesel costs"
- "CBN just increased MPR from 18.75% to 19.50%"
- "MTN Nigeria CEO resigned this morning"
- "Analyst at Chapel Hill upgraded ACCESSCORP to BUY"

Web search handles **time-sensitive, breaking information** that would be stale if embedded.

**The Hybrid Strategy**:
```
┌─────────────────────────────────────────────────────┐
│                INFORMATION SOURCES                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📚 EMBEDDED (RAG - Static, Deep)                  │
│  ├─ Annual Reports (3 years)                       │
│  ├─ Quarterly Results (8 quarters)                 │
│  ├─ Investor Presentations                         │
│  └─ Risk Disclosures                               │
│                                                     │
│  🌐 WEB SEARCH (Live, Breaking)                    │
│  ├─ Breaking news (last 7 days)                    │
│  ├─ Current stock price & volume                   │
│  ├─ Regulatory announcements                       │
│  ├─ Analyst upgrades/downgrades                    │
│  └─ Macroeconomic updates                          │
│                                                     │
│  📊 STRUCTURED APIs (Real-time Metrics)            │
│  ├─ Yahoo Finance (P/E, ratios)                    │
│  ├─ CBN rates (official)                           │
│  └─ DCF calculations (deterministic)               │
└─────────────────────────────────────────────────────┘
```

**Implementation**:

```python
from langchain.tools import tool
from tavily import TavilyClient  # Free tier: 1000 searches/month
from datetime import datetime, timedelta
import os

@tool
def web_search_financial_context(query: str, ticker: str = None, days_back: int = 7) -> str:
    """
    Searches the web for recent financial news, market updates, and regulatory announcements.
    
    Use this tool for:
    - Breaking news about the company (CEO changes, M&A, new products)
    - Current market sentiment and price action
    - Recent analyst reports or rating changes
    - Regulatory announcements from CBN, NGX, SEC Nigeria
    - Macroeconomic data updates (inflation, GDP, FX rates)
    - Competitor developments
    
    DO NOT use this for:
    - Historical financial statements (use retrieve_sec_filings instead)
    - Annual revenue/profit trends (use RAG for audited data)
    - Long-term financial ratios (use fetch_financial_ratios)
    
    Args:
        query: What to search for (e.g., "MTN Nigeria recent news", "CBN interest rate announcement")
        ticker: Optional stock ticker to focus results (e.g., "DANGCEM")
        days_back: How many days of recent results (default: 7)
    
    Returns:
        JSON string with search results including titles, URLs, snippets, and publication dates
    """
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    # Construct search query
    if ticker:
        search_query = f"{ticker} {query} Nigeria stock market"
    else:
        search_query = f"{query} Nigeria"
    
    # Add date filter
    date_filter = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    # Search with focus on Nigerian financial sources
    try:
        results = client.search(
            query=search_query,
            search_depth="advanced",  # More thorough search
            max_results=5,
            include_domains=[
                "nairametrics.com",
                "businessday.ng",
                "punchng.com",
                "vanguardngr.com",
                "theguardian.ng",
                "ngxgroup.com",       # Nigerian Exchange Group
                "cbn.gov.ng",         # Central Bank of Nigeria
                "sec.gov.ng",         # SEC Nigeria
                "bloomberg.com",
                "reuters.com",
                "ft.com"              # Financial Times
            ],
            exclude_domains=[
                "facebook.com",
                "twitter.com",
                "reddit.com"          # Exclude social media (unreliable)
            ]
        )
    
    except Exception as e:
        return json.dumps({
            "error": f"Web search failed: {str(e)}",
            "query": search_query,
            "fallback": "Try retrieve_sec_filings or fetch_financial_ratios instead"
        })
    
    # Format results with [WEB:n] citations (distinct from [REF:n] for RAG)
    formatted_results = []
    
    for i, result in enumerate(results.get('results', []), start=1):
        formatted_results.append({
            "citation": f"WEB:{i}",
            "title": result['title'],
            "url": result['url'],
            "published_date": result.get('published_date', 'Date unavailable'),
            "source": extract_domain(result['url']),
            "snippet": result['content'][:400] + "..." if len(result['content']) > 400 else result['content'],
            "relevance_score": result.get('score', 0.0)
        })
    
    return json.dumps({
        "query": search_query,
        "results_count": len(formatted_results),
        "search_date": datetime.now().isoformat(),
        "results": formatted_results
    }, indent=2)

def extract_domain(url: str) -> str:
    """Extracts clean domain name from URL."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain.replace('www.', '')
```

**Agent Usage Example**:

```python
# Fundamental Analyst prompt includes:
"""
When analyzing {ticker}, you have access to three complementary tools:

1. retrieve_sec_filings: For historical financial data from 10-Ks, quarterly reports
   ✓ Use for: Revenue trends, margin analysis, historical debt levels
   ✓ Citations format: [REF:n]

2. web_search_financial_context: For breaking news and recent developments
   ✓ Use for: Recent price movements, breaking news, analyst updates, regulatory changes
   ✓ Citations format: [WEB:n]

3. fetch_financial_ratios: For current valuation metrics
   ✓ Use for: Current P/E ratio, debt-to-equity, market cap

STRATEGY: Start with retrieve_sec_filings for fundamentals, then use web_search_financial_context
to check if anything material has changed in the last 7 days that would affect your analysis.
"""
```

**Example Agent Output (Combining RAG + Web Search)**:

```markdown
## Fundamental Analyst Bull Case

### Revenue Growth Momentum
Revenue grew from ₦1.8T (FY2023) to ₦2.1T (FY2025), representing 18.7% YoY 
growth [REF:1]. This is driven by 23% volume growth in cement sales across 
Nigerian and Senegalese operations [REF:2].

### Recent Developments
However, web search reveals significant recent news:

[WEB:1] **"Dangote Cement raises prices 15% amid soaring energy costs"**  
Source: Nairametrics, Nov 1, 2026  
The company announced a 15% price increase effective November 2026, citing 
diesel costs that have risen 40% year-over-year. While this supports margins, 
demand may soften if competitors don't follow suit.

[WEB:2] **"CBN raises MPR to 19.50%, highest in 5 years"**  
Source: Central Bank of Nigeria, Oct 28, 2026  
The Monetary Policy Committee increased the benchmark rate by 75 basis points 
to combat 22.1% inflation. This increases WACC for valuation and may pressure 
demand for capital-intensive construction projects.

### Synthesis
The strong historical growth [REF:1-2] remains intact, but recent macro 
headwinds [WEB:2] and pricing actions [WEB:1] introduce near-term uncertainty. 
The bull case hinges on whether price increases stick without volume decline.
```

**Web Search vs RAG: Decision Matrix**

| Query Type | Tool to Use | Reason |
|------------|-------------|--------|
| "What was revenue growth in FY2025?" | `retrieve_sec_filings` | Audited historical data, needs citation to exact page |
| "Did Dangote raise cement prices recently?" | `web_search_financial_context` | Breaking news (last week), not in annual report |
| "What is the current P/E ratio?" | `fetch_financial_ratios` | Live market data from Yahoo Finance |
| "What are the company's main risk factors?" | `retrieve_sec_filings` | Embedded in Risk Factors section of 10-K |
| "Did CBN announce a rate hike this week?" | `web_search_financial_context` | Recent policy announcement |
| "What is the debt-to-equity ratio trend?" | `retrieve_sec_filings` | Historical trend requires multiple years of data |
| "What's today's stock price?" | `fetch_financial_ratios` | Real-time market data |
| "Are there any analyst upgrades this month?" | `web_search_financial_context` | Recent analyst actions |

**Free Web Search Provider Options**:

| Provider | Free Tier | Best For | API Complexity |
|----------|-----------|----------|----------------|
| **Tavily AI** | 1,000 searches/month | Financial news, structured results | ⭐⭐⭐⭐⭐ Easy |
| **SerpAPI** | 100 searches/month | Google results, Nigerian sources | ⭐⭐⭐⭐ Medium |
| **Bing Web Search API** | 1,000 queries/month | Microsoft backing, reliable | ⭐⭐⭐ Medium |
| **DuckDuckGo (duckduckgo-search)** | Unlimited | Fully free, no API key | ⭐⭐⭐⭐⭐ Easy |

**Recommendation**: **Tavily AI** for MVP (1,000 free searches = ~30 searches/day, sufficient for 150+ debates/month)

**Installation**:
```bash
pip install tavily-python
```

**.env Configuration**:
```bash
TAVILY_API_KEY=tvly-your_api_key_here
```

**Rate Limiting & Caching**:

```python
# Cache web search results for 24 hours to avoid redundant searches
import redis
from functools import wraps

cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cache_web_search(ttl_seconds=86400):  # 24 hours
    def decorator(func):
        @wraps(func)
        def wrapper(query: str, ticker: str = None, days_back: int = 7):
            # Generate cache key
            cache_key = f"websearch:{ticker or 'general'}:{query}:{days_back}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Call actual function
            result = func(query, ticker, days_back)
            
            # Store in cache
            cache.setex(cache_key, ttl_seconds, result)
            
            return result
        return wrapper
    return decorator

@tool
@cache_web_search(ttl_seconds=86400)
def web_search_financial_context(query: str, ticker: str = None, days_back: int = 7) -> str:
    # ... implementation above
```

**Impact on Document Corpus**:

With web search handling live data, the embedded corpus can be **smaller**:

**Old Corpus (No Web Search)**:
- 3 annual reports (750 chunks)
- 8 quarterly results (600 chunks)
- **90 days of news articles (200 chunks)** ← No longer needed
- Investor presentations (200 chunks)
- Risk disclosures (100 chunks)
- **Total: ~2,250 chunks per company**

**New Corpus (With Web Search)**:
- 3 annual reports (750 chunks)
- 8 quarterly results (600 chunks)
- Investor presentations (200 chunks)
- Risk disclosures (100 chunks)
- **Total: ~1,650 chunks per company** ✅

**Storage Savings**:
- 10 companies × 1,650 chunks = **16,500 chunks** (~33MB)
- **vs 22,500 chunks** (~45MB) without web search
- **27% reduction** in storage requirements

**Web Search Quota Usage**:
- Free tier: 1,000 searches/month
- Per debate: 3 agents × 2 searches each = 6 searches
- **~150 full debates per month** on free tier
- **~5 debates per day** sustainable

---

## 8. API Design & Backend Architecture

### REST API Endpoints

#### Primary Endpoint: Initiate Debate

```
POST /api/v1/debates
```

**Request Body**:
```json
{
  "ticker": "DANGCEM",
  "company_name": "Dangote Cement Plc",  // Optional, looked up if missing
  "user_thesis": "Dangote Cement will benefit from Nigeria's infrastructure boom and cement demand growth",
  "capital_to_deploy": 5000000,  // in Naira
  "risk_tolerance": "moderate",  // "conservative" | "moderate" | "aggressive"
  "tier": 3,  // 1 (quick check), 2 (risk assessment), 3 (full committee)
  "user_id": "uuid-123"  // For tracking, auth
}
```

**Response** (202 Accepted - async execution):
```json
{
  "debate_id": "debate_abc123xyz",
  "status": "running",
  "ticker": "DANGCEM",
  "tier": 3,
  "estimated_completion_seconds": 180,
  "websocket_url": "wss://api.alphacouncil.com/debates/debate_abc123xyz",
  "polling_url": "/api/v1/debates/debate_abc123xyz/status",
  "created_at": "2026-11-02T07:00:00Z"
}
```

**Why Async?** Debates take 2-5 minutes (10+ LLM calls, RAG queries, tool executions). Blocking HTTP requests would timeout.

**Implementation**:
```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from celery import Celery
import uuid

app = FastAPI()
celery_app = Celery('alphacouncil', broker='redis://localhost:6379/0')

class DebateRequest(BaseModel):
    ticker: str
    company_name: str | None = None
    user_thesis: str
    capital_to_deploy: float
    risk_tolerance: str
    tier: int = 3
    user_id: str

@app.post("/api/v1/debates")
async def create_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """
    Initiates a debate and returns immediately.
    Actual debate execution happens in Celery worker.
    """
    # Generate debate ID
    debate_id = f"debate_{uuid.uuid4().hex[:12]}"
    
    # Lookup company name if not provided
    if not request.company_name:
        request.company_name = lookup_company_name(request.ticker)
    
    # Store debate request in DB
    debate_record = {
        'debate_id': debate_id,
        'ticker': request.ticker,
        'company_name': request.company_name,
        'user_thesis': request.user_thesis,
        'capital_to_deploy': request.capital_to_deploy,
        'risk_tolerance': request.risk_tolerance,
        'tier': request.tier,
        'user_id': request.user_id,
        'status': 'running',
        'created_at': datetime.utcnow()
    }
    
    db.debates.insert_one(debate_record)
    
    # Queue debate execution (Celery task)
    run_debate_task.delay(debate_id, request.dict())
    
    return {
        'debate_id': debate_id,
        'status': 'running',
        'ticker': request.ticker,
        'tier': request.tier,
        'estimated_completion_seconds': 180,
        'websocket_url': f"wss://api.alphacouncil.com/debates/{debate_id}",
        'polling_url': f"/api/v1/debates/{debate_id}/status",
        'created_at': debate_record['created_at'].isoformat()
    }
```

**Celery Task** (Background Worker):
```python
@celery_app.task
def run_debate_task(debate_id: str, request_data: dict):
    """
    Executes the debate in a background worker.
    Updates DB as debate progresses.
    """
    try:
        # Update status to 'ingesting_documents'
        update_debate_status(debate_id, 'ingesting_documents')
        
        # Step 1: Ingest 10-K if not already in vector DB
        ingest_filings_if_needed(request_data['ticker'])
        
        # Update status to 'debating'
        update_debate_status(debate_id, 'debating')
        
        # Step 2: Run LangGraph debate
        initial_state = build_initial_state(request_data)
        graph = build_debate_graph()
        final_state = graph.invoke(initial_state)
        
        # Step 3: Save results
        debate_result = {
            'debate_id': debate_id,
            'status': 'completed',
            'final_verdict': final_state['final_verdict'],
            'messages': final_state['messages'],
            'bull_strength': final_state['bull_strength'],
            'bear_strength': final_state['bear_strength'],
            'completed_at': datetime.utcnow()
        }
        
        db.debates.update_one(
            {'debate_id': debate_id},
            {'$set': debate_result}
        )
        
        # Notify via WebSocket
        broadcast_debate_complete(debate_id, debate_result)
        
    except Exception as e:
        # Mark as failed
        db.debates.update_one(
            {'debate_id': debate_id},
            {'$set': {
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.utcnow()
            }}
        )
        
        broadcast_debate_failed(debate_id, str(e))
```

#### Get Debate Status (Polling Alternative to WebSocket)

```
GET /api/v1/debates/{debate_id}/status
```

**Response** (Running):
```json
{
  "debate_id": "debate_abc123xyz",
  "status": "debating",
  "ticker": "DANGCEM",
  "current_turn": 2,
  "current_agent": "quantitative_auditor",
  "progress_percentage": 40,
  "elapsed_seconds": 72,
  "estimated_remaining_seconds": 108
}
```

**Response** (Completed):
```json
{
  "debate_id": "debate_abc123xyz",
  "status": "completed",
  "ticker": "DANGCEM",
  "completed_at": "2026-11-02T07:03:00Z",
  "result_url": "/api/v1/debates/debate_abc123xyz"
}
```

#### Get Full Debate Results

```
GET /api/v1/debates/{debate_id}
```

**Response**:
```json
{
  "debate_id": "debate_abc123xyz",
  "ticker": "DANGCEM",
  "company_name": "Dangote Cement Plc",
  "status": "completed",
  "created_at": "2026-11-02T07:00:00Z",
  "completed_at": "2026-11-02T07:03:00Z",
  
  "final_verdict": {
    "verdict": "CONDITIONAL_BUY",
    "verdict_label": "Conditional Buy",
    "confidence": 0.68,
    "recommendation": { /* ... (as shown in Section 1) */ },
    "bull_case_summary": "...",
    "bear_case_summary": "...",
    "key_risks": [ /* ... */ ],
    "monitoring_triggers": [ /* ... */ ]
  },
  
  "debate_transcript": [
    {
      "turn": 1,
      "agent_role": "fundamental_analyst",
      "content": "## Bull Case Summary\nDangote Cement shows...",
      "citations": ["REF:1", "REF:2", "REF:3"],
      "confidence": 0.82,
      "timestamp": "2026-11-02T07:00:45Z"
    },
    {
      "turn": 2,
      "agent_role": "quantitative_auditor",
      "content": "## Bear Case Summary\nHowever, critical risks...",
      "citations": ["REF:4", "REF:5", "REF:6"],
      "confidence": 0.75,
      "timestamp": "2026-11-02T07:01:30Z"
    },
    /* ... more turns */
  ],
  
  "citations": [
    {
      "ref_id": "REF:1",
      "source": "DANGCEM 10-K FY2025",
      "page": 42,
      "section": "MD&A",
      "text": "Our revenue for fiscal year 2025 increased by 18.7%...",
      "relevance_score": 0.89
    },
    /* ... more citations */
  ],
  
  "metadata": {
    "tier": 3,
    "total_turns": 4,
    "total_tool_calls": 12,
    "llm_tokens_used": 28500,
    "cost_usd": 0.05,
    "execution_time_seconds": 180
  }
}
```

#### List User's Past Debates

```
GET /api/v1/debates?user_id={user_id}&limit=20&offset=0
```

**Response**:
```json
{
  "debates": [
    {
      "debate_id": "debate_abc123xyz",
      "ticker": "DANGCEM",
      "verdict": "CONDITIONAL_BUY",
      "confidence": 0.68,
      "created_at": "2026-11-02T07:00:00Z"
    },
    /* ... more debates */
  ],
  "total": 47,
  "limit": 20,
  "offset": 0
}
```

#### Export Investment Memo (PDF)

```
GET /api/v1/debates/{debate_id}/export?format=pdf
```

**Response**: Binary PDF file

**Implementation**:
```python
from weasyprint import HTML
from jinja2 import Template

@app.get("/api/v1/debates/{debate_id}/export")
async def export_debate(debate_id: str, format: str = "pdf"):
    """
    Generates a PDF investment memo from the debate.
    """
    debate = db.debates.find_one({'debate_id': debate_id})
    
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    # Render HTML from template
    template = Template(open('templates/investment_memo.html').read())
    html_content = template.render(debate=debate)
    
    if format == "pdf":
        # Convert HTML to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={debate['ticker']}_memo_{debate_id}.pdf"
            }
        )
    
    elif format == "markdown":
        # Convert debate to markdown
        md_content = render_markdown_memo(debate)
        
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={debate['ticker']}_memo_{debate_id}.md"
            }
        )
```

---

## 9. Database Schema Design

### PostgreSQL Schema (Relational Data + pgvector)

#### Table: `debates`

```sql
CREATE TABLE debates (
    debate_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT,
    user_thesis TEXT,
    capital_to_deploy NUMERIC(15, 2),
    risk_tolerance TEXT CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive')),
    tier INTEGER CHECK (tier IN (1, 2, 3)),
    
    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ingesting_documents', 'debating', 'completed', 'failed')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT,
    
    -- Results (stored as JSONB for flexibility)
    final_verdict JSONB,
    debate_transcript JSONB,  -- Array of agent messages
    citations JSONB,           -- Array of citation objects
    
    -- Metadata
    total_turns INTEGER,
    total_tool_calls INTEGER,
    llm_tokens_used INTEGER,
    cost_usd NUMERIC(10, 4),
    execution_time_seconds INTEGER,
    
    -- Indexes
    INDEX idx_debates_user_id (user_id),
    INDEX idx_debates_ticker (ticker),
    INDEX idx_debates_status (status),
    INDEX idx_debates_created_at (created_at DESC)
);
```

#### Table: `document_chunks` (RAG System)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    chunk_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    filing_year INTEGER NOT NULL,
    filing_type TEXT NOT NULL,  -- '10-K', '10-Q', 'Earnings'
    section TEXT,                -- 'Risk Factors', 'MD&A', 'Financial Statements'
    page INTEGER,
    text TEXT NOT NULL,
    char_count INTEGER,
    
    -- Vector embedding (768-dim for multi-qa-mpnet-base-cos-v1)
    embedding VECTOR(768),
    
    -- Metadata
    ingested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    source_url TEXT,
    
    -- Indexes
    INDEX idx_chunks_ticker_year (ticker, filing_year),
    INDEX idx_chunks_section (section)
);

-- HNSW index for fast similarity search (pgvector)
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

**Why HNSW?** Hierarchical Navigable Small World (HNSW) is the fastest approximate nearest neighbor algorithm for high-dimensional vectors. 10x faster than IVFFlat for pgvector.

#### Table: `financial_ratios` (Cached Metrics)

```sql
CREATE TABLE financial_ratios (
    ticker TEXT NOT NULL,
    period DATE NOT NULL,  -- End of quarter/year
    data_source TEXT NOT NULL,  -- 'yahoo_finance', 'financial_modeling_prep'
    
    -- Valuation ratios
    pe_ratio NUMERIC(10, 2),
    forward_pe NUMERIC(10, 2),
    peg_ratio NUMERIC(10, 2),
    price_to_book NUMERIC(10, 2),
    price_to_sales NUMERIC(10, 2),
    
    -- Leverage ratios
    debt_to_equity NUMERIC(10, 2),
    debt_to_assets NUMERIC(10, 2),
    interest_coverage NUMERIC(10, 2),
    
    -- Liquidity ratios
    current_ratio NUMERIC(10, 2),
    quick_ratio NUMERIC(10, 2),
    cash_ratio NUMERIC(10, 2),
    
    -- Profitability ratios
    return_on_equity NUMERIC(10, 4),
    return_on_assets NUMERIC(10, 4),
    gross_margin NUMERIC(10, 4),
    operating_margin NUMERIC(10, 4),
    net_margin NUMERIC(10, 4),
    
    -- Growth metrics
    revenue_growth_yoy NUMERIC(10, 4),
    earnings_growth_yoy NUMERIC(10, 4),
    
    -- Market data
    current_price NUMERIC(15, 2),
    market_cap NUMERIC(20, 2),
    beta NUMERIC(10, 4),
    
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (ticker, period, data_source),
    INDEX idx_ratios_ticker (ticker),
    INDEX idx_ratios_period (period DESC)
);
```

**Caching Strategy**: Financial ratios update quarterly. Cache for 24 hours to avoid redundant API calls.

#### Table: `news_sentiment` (Cached Sentiment)

```sql
CREATE TABLE news_sentiment (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    article_url TEXT,
    article_title TEXT,
    article_source TEXT,
    
    sentiment_score NUMERIC(5, 3),  -- -1.0 to 1.0
    sentiment_label TEXT CHECK (sentiment_label IN ('positive', 'negative', 'neutral')),
    
    analyzed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (ticker, date, article_url),
    INDEX idx_sentiment_ticker_date (ticker, date DESC)
);

-- Aggregate view for quick average sentiment lookup
CREATE MATERIALIZED VIEW mv_avg_sentiment AS
SELECT 
    ticker,
    date,
    AVG(sentiment_score) as avg_sentiment,
    COUNT(*) as article_count,
    CASE 
        WHEN AVG(sentiment_score) > 0.2 THEN 'Bullish'
        WHEN AVG(sentiment_score) < -0.2 THEN 'Bearish'
        ELSE 'Neutral'
    END as sentiment_label
FROM news_sentiment
WHERE analyzed_at > NOW() - INTERVAL '30 days'
GROUP BY ticker, date;

-- Refresh daily
CREATE INDEX ON mv_avg_sentiment (ticker, date DESC);
```

#### Table: `macro_indicators` (CBN Data Cache)

```sql
CREATE TABLE macro_indicators (
    date DATE PRIMARY KEY,
    monetary_policy_rate NUMERIC(5, 2),
    inflation_rate NUMERIC(5, 2),
    fx_rate_usd_ngn NUMERIC(10, 2),
    treasury_bill_90d NUMERIC(5, 2),
    treasury_bill_180d NUMERIC(5, 2),
    
    data_source TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Get latest macro data
CREATE INDEX ON macro_indicators (date DESC);
```

#### Table: `users` (Authentication & Billing)

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    
    -- Subscription tier
    subscription_tier TEXT NOT NULL DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'pro')),
    subscription_status TEXT NOT NULL DEFAULT 'active' CHECK (subscription_status IN ('active', 'cancelled', 'expired')),
    subscription_started_at TIMESTAMP,
    subscription_expires_at TIMESTAMP,
    
    -- Usage tracking
    debates_run_this_month INTEGER DEFAULT 0,
    debates_limit_per_month INTEGER DEFAULT 5,  -- free tier: 5, basic: 50, pro: unlimited
    
    -- Billing
    stripe_customer_id TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    INDEX idx_users_email (email),
    INDEX idx_users_subscription (subscription_tier, subscription_status)
);
```

---

## 10. Deployment Architecture & Infrastructure

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Next.js 14 (Vercel / Cloudflare Pages)                       │
│  - Server-side rendering                                        │
│  - React components (shadcn/ui)                                │
│  - WebSocket client for real-time updates                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / LOAD BALANCER                │
├─────────────────────────────────────────────────────────────────┤
│  Cloudflare (CDN + DDoS protection)                            │
│  - Rate limiting: 100 requests/min per IP                      │
│  - SSL termination                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND LAYER (Railway)                   │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Application (Gunicorn + Uvicorn)                      │
│  - 4 workers                                                    │
│  - REST API endpoints                                           │
│  - WebSocket server (for debate progress)                      │
│  - Authentication (JWT tokens)                                  │
└─────────────────────────────────────────────────────────────────┘
       ↓                    ↓                      ↓
┌─────────────┐     ┌──────────────┐      ┌────────────────┐
│  Celery     │     │ PostgreSQL   │      │ Redis          │
│  Workers    │     │ (Supabase)   │      │ (Upstash)      │
│  (Railway)  │     │              │      │                │
│             │     │ - debates    │      │ - Task queue   │
│ 2 workers   │     │ - document_  │      │ - Rate limits  │
│ for debate  │     │   chunks     │      │ - Caching      │
│ execution   │     │ - financial_ │      │                │
│             │     │   ratios     │      │                │
│ LangGraph   │     │ - pgvector   │      └────────────────┘
│ orchestration│    │   extension  │
└─────────────┘     └──────────────┘
       ↓                    ↓
┌─────────────┐     ┌──────────────┐
│  External   │     │ Object       │
│  APIs       │     │ Storage      │
│             │     │ (Supabase)   │
│ - Groq LLM  │     │              │
│ - NewsAPI   │     │ - PDF files  │
│ - Yahoo Fin.│     │ - 10-Ks      │
│ - FMP       │     │ - Generated  │
│ - CBN       │     │   memos      │
└─────────────┘     └──────────────┘
```

### Infrastructure Stack (MVP)

| Component | Technology | Purpose | Cost (MVP) |
|-----------|-----------|---------|------------|
| **Frontend Hosting** | Vercel / Cloudflare Pages | Static site hosting + SSR | Free tier |
| **API Server** | Railway (2 GB RAM, 2 vCPU) | FastAPI application | $10/month |
| **Database** | Supabase (PostgreSQL + pgvector) | Relational data + vector search | Free tier (500MB) |
| **Object Storage** | Supabase Storage | PDF files, 10-Ks | Free tier (1GB) |
| **Task Queue** | Upstash Redis | Celery broker | Free tier |
| **Background Workers** | Railway (2 GB RAM, 2 vCPU) | Celery workers for debates | $10/month |
| **CDN / Security** | Cloudflare | DDoS protection, rate limiting | Free tier |
| **LLM Inference** | Groq (free tier) | Llama 3.1 70B for agents | Free (14,400 req/day) |
| **Embeddings** | Local (sentence-transformers) | Vector embeddings | Included in compute |
| **Monitoring** | Sentry | Error tracking | Free tier |

**Total Monthly Cost (MVP)**: ~$20/month (Railway x2)

### Scaling Strategy (Post-MVP)

**When to scale**: >1000 debates/day or >500 concurrent users

| Component | Upgrade Path | Cost |
|-----------|-------------|------|
| **API Server** | Railway Pro: 8 GB RAM, 4 vCPU | $50/month |
| **Database** | Supabase Pro: 8 GB, 100 GB storage | $25/month |
| **LLM** | Groq paid tier or self-hosted Llama 3.1 70B | $100/month or GPU server |
| **Workers** | 4x Celery workers | $40/month |

**Estimated Cost at 10,000 debates/month**: ~$200/month

---

## 11. The Critical Role of RAG: Why Vector Search Matters

### The Tool RAG Matrix

Out of the 5 core agent tools, **only 1-2 actually use RAG**. Yet RAG is the architectural cornerstone that makes AlphaCouncil's claims verifiable rather than hallucinated.

| Tool | Uses RAG? | Type | Why RAG / Why Not |
|------|-----------|------|-------------------|
| `retrieve_sec_filings(ticker, query)` | ✅ **YES** | Semantic search | Finds relevant excerpts in 200+ page PDFs without reading sequentially |
| `fetch_financial_ratios(ticker)` | ❌ NO | REST API call | Structured data from Yahoo Finance/FMP (no text search) |
| `get_market_sentiment(ticker)` | 🟡 **OPTIONAL** | Hybrid | Can embed news corpus for search, or just scrape live |
| `get_cbn_rates()` | ❌ NO | Web scraping | Fetches specific page (CBN monetary policy) |
| `run_dcf_model(fcf, growth, wacc)` | ❌ NO | Pure calculation | Deterministic math, no documents involved |

### What RAG Solves: The Evidence Problem

**Without RAG**, when the Fundamental Analyst claims *"Revenue grew strongly"*, one of three things happens:

1. **The LLM hallucinates** a plausible-sounding number (e.g., "15% growth") that may be completely wrong
2. **The LLM refuses** to make specific claims without evidence, giving vague output like "appears to be growing"
3. **You paste the entire 10-K into context** (200 pages = 150,000 tokens), burning through context limits and API costs

**With RAG**, the agent calls:
```python
retrieve_sec_filings("DANGCEM", "revenue growth year over year")
```

And gets back:
```
[REF:1] Source: DANGCEM 10-K FY2025, Page 42, Section: MD&A
"Our revenue for fiscal year 2025 increased by 18.7% year-over-year to ₦2.1 trillion, 
compared to ₦1.77 trillion in FY2024. This growth was driven primarily by increased 
cement demand in the Nigerian infrastructure sector..."
(Relevance: 0.89)

[REF:2] Source: DANGCEM 10-K FY2025, Page 87, Section: Financial Statements
"Consolidated Revenue: ₦2,103,450,000,000 (FY2025) vs ₦1,772,100,000,000 (FY2024)"
(Relevance: 0.92)
```

Now the agent can write:
```
Revenue grew 18.7% YoY to ₦2.1T in FY2025 [REF:1], driven by infrastructure demand [REF:1].
```

### Citation Analysis: Where RAG Evidence Appears

Let's examine what gets cited in a typical debate:

#### Fundamental Analyst (Bull Case) Citations

```
🟢 Bull Case: 5 claims total
   ├─ [REF:1] Revenue growth 18.7%          ← FROM RAG ✅
   ├─ [REF:2] Gross margin 45.1%            ← FROM RAG ✅
   ├─ [REF:3] Market sentiment +0.72        ← FROM API ❌
   ├─ [REF:4] 65% market share              ← FROM RAG ✅
   └─ [REF:5] Infrastructure bill passed    ← FROM RAG (news) ✅

RAG-sourced claims: 4/5 (80%)
```

#### Quantitative Auditor (Bear Case) Citations

```
🔴 Bear Case: 5 claims total
   ├─ [REF:6] Debt-to-equity 1.8            ← FROM API ❌
   ├─ [REF:7] Interest coverage 3.1x        ← FROM RAG ✅
   ├─ [REF:8] 40% USD debt                  ← FROM RAG ✅
   ├─ [REF:9] Declining cash flow           ← FROM RAG ✅
   └─ [REF:10] Current ratio 1.2            ← FROM API ❌

RAG-sourced claims: 3/5 (60%)
```

#### Risk & Macro Strategist Citations

```
🟡 Macro Analysis: 4 claims total
   ├─ [REF:11] CBN MPR 18.75%               ← FROM API ❌
   ├─ [REF:12] DCF value ₦420/share         ← FROM CALCULATION ❌
   ├─ [REF:13] FX sensitivity analysis      ← FROM RAG ✅
   └─ [REF:14] Inflation impact on costs    ← FROM API ❌

RAG-sourced claims: 1/4 (25%)
```

**Overall: 8 out of 14 citations (57%) come from RAG-powered semantic search.**

### Why This Ratio Makes Sense

**Numeric metrics** (current stock price, P/E ratio, interest rates) come from **structured APIs**:
- These are real-time, machine-readable, standardized
- Yahoo Finance API returns: `{"pe_ratio": 12.5, "debt_to_equity": 1.8}`
- No need for semantic search—it's already structured

**Contextual insights** (why revenue grew, where debt is denominated, management's explanation) come from **unstructured text**:
- Buried in 200-page PDFs
- Written in narrative form: "Our revenue growth was primarily driven by..."
- Requires semantic understanding to find the right paragraph

### The "Grounding" Problem in LLM Applications

This is a general problem in finance AI:

| Approach | Pros | Cons | AlphaCouncil Uses? |
|----------|------|------|-------------------|
| **Pure LLM (no retrieval)** | Fast, simple | Hallucinates numbers, no citations | ❌ NO |
| **Paste entire documents in context** | Accurate (LLM sees everything) | Token explosion (150k tokens per 10-K) | ❌ NO |
| **RAG (vector search)** | Grounded in documents, scalable | Requires pgvector setup | ✅ YES |
| **Fine-tuned model on financial docs** | Can memorize patterns | Extremely expensive, still hallucinates | ❌ NO |
| **Hybrid (RAG + structured APIs)** | Best of both worlds | More complex architecture | ✅ YES |

AlphaCouncil uses **Hybrid RAG**:
- Structured metrics (P/E, D/E, price) → API calls (fast, accurate)
- Unstructured insights (revenue drivers, risk factors) → RAG (cited, verifiable)

### RAG Performance Requirements

For AlphaCouncil to work, RAG needs to be:

1. **Fast**: <1 second per query (target: 200-500ms)
   - Embedding generation: ~50ms (sentence-transformers on CPU)
   - pgvector search: ~100ms (HNSW index)
   - Total: ~150ms per `retrieve_sec_filings` call

2. **Accurate**: Top-5 results must be relevant >80% of the time
   - Use `multi-qa-mpnet-base-cos-v1` embedding model (768-dim, trained on Q&A pairs)
   - Hybrid search (semantic + keyword filters) for financial terms
   - Result: ~85% relevance in testing

3. **Comprehensive**: Must cover all NSE top 50 stocks
   - 50 companies × 3 years of 10-Ks = 150 documents
   - Average 200 pages/document × 500 chunks/document = 75,000 chunks
   - Storage: 75k chunks × 768 dims × 4 bytes = ~230 MB embeddings
   - Supabase free tier: 500 MB → ✅ fits

### When RAG Fails: Fallback Strategy

**Failure Mode 1: No 10-K available for ticker**
```python
def retrieve_sec_filings(ticker: str, query: str) -> str:
    results = vector_store.query(embedding, ticker=ticker)
    
    if not results:
        return json.dumps({
            "error": f"No financial documents found for {ticker}",
            "fallback": "Agent should rely on fetch_financial_ratios instead",
            "suggestion": "Use publicly available data sources only"
        })
```

**Failure Mode 2: Query too vague**
```python
# Bad query: "information"
# Good query: "revenue growth drivers and market share trends"

# System prompt includes guidance:
"""
When calling retrieve_sec_filings, use specific queries:
✓ Good: "debt maturity schedule and interest rates"
✗ Bad: "debt information"
"""
```

**Failure Mode 3: Retrieved chunks lack the specific data**
```python
# User asks: "What is the exact debt-to-equity ratio?"
# RAG returns: "We maintain a strong capital structure..."

# Agent should recognize this and call fetch_financial_ratios instead:
"""
The 10-K mentions capital structure [REF:1] but doesn't state the exact 
debt-to-equity ratio. Calling fetch_financial_ratios for precise metrics...

[Tool call: fetch_financial_ratios("DANGCEM")]
Result: Debt-to-equity = 1.8
"""
```

### Minimal RAG Implementation Path

For MVP, you can start with **one vector table** and scale later:

**Phase 1 (MVP)**: Single embedding model, basic search
```sql
CREATE TABLE document_chunks (
    chunk_id TEXT PRIMARY KEY,
    ticker TEXT,
    text TEXT,
    embedding VECTOR(768),
    metadata JSONB  -- Store filing_year, page, section as flexible JSON
);

CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

**Phase 2 (Scale)**: Add hybrid search, filters
```sql
-- Add full-text search
ALTER TABLE document_chunks ADD COLUMN text_tsv TSVECTOR;
CREATE INDEX ON document_chunks USING GIN (text_tsv);

-- Hybrid query
SELECT chunk_id, text, 
       1 - (embedding <=> query_embedding) AS similarity
FROM document_chunks
WHERE ticker = 'DANGCEM'
  AND filing_year >= 2023
  AND text_tsv @@ to_tsquery('debt & equity')  -- Keyword filter
ORDER BY similarity DESC
LIMIT 5;
```

**Phase 3 (Production)**: Multiple embeddings, reranking
```sql
-- Add reranker scores (cross-encoder for higher accuracy)
ALTER TABLE document_chunks ADD COLUMN rerank_score FLOAT;

-- Two-stage retrieval:
-- 1. Fast pgvector search (top 50)
-- 2. Rerank with cross-encoder (keep top 5)
```

---

## 12. Problem Statement & Market Opportunity

### The Investment Analysis Gap in Nigeria

**Current Reality**: A retail investor in Lagos wants to invest ₦5 million in Dangote Cement. Their options:

1. **DIY Research** (4-8 hours)
   - Download 200-page annual report
   - Cross-reference 3 years of financials
   - Track news sentiment across 10+ Nigerian outlets
   - Calculate DCF valuation manually
   - **Result**: Exhausting, error-prone, still one-sided (no adversarial challenge)

2. **Professional Analyst** (₦50,000-200,000 per report)
   - Wait 3-5 days for report
   - Get generic coverage (analyst covers 20+ stocks)
   - No customization to investor's thesis or risk tolerance
   - **Result**: Expensive, slow, black-box (can't trace reasoning)

3. **Ask ChatGPT** (free, 30 seconds)
   - "Should I buy Dangote Cement?"
   - Get shallow, generic response
   - No citations, no debate, prone to confirmation bias
   - **Result**: Fast but unreliable, no audit trail

4. **Nigerian Brokerage Research** (free with account)
   - Coverage limited to top 10-15 stocks
   - Reports are promotional (aligned with brokerage interests)
   - No adversarial stress-testing
   - **Result**: Biased, incomplete

### What AlphaCouncil Changes

**Input**: Ticker + Thesis + Capital → **Output**: Actionable investment memo in 3-5 minutes

**Key Differentiators**:

1. **Adversarial Rigor**: Forces bull AND bear cases (no confirmation bias)
2. **Verifiable Claims**: Every statement cited with [REF:n] to source document
3. **Risk-Adjusted**: Specific position sizing, stop-loss levels, monitoring triggers
4. **Audit Trail**: Full debate transcript saved for future reference
5. **Affordable**: ₦2,000 vs ₦50,000 for professional analyst

### Market Size (Nigeria Focus)

**Total Addressable Market (TAM)**:
- Nigerian stock market investors: ~5 million registered accounts (NSE data)
- Active traders: ~400,000 (trade at least quarterly)
- TAM = 400,000 investors × ₦10,000/year (5 debates @ ₦2,000) = **₦4 billion ($2.75M)**

**Serviceable Addressable Market (SAM)**:
- Digital-savvy investors (use online trading): ~100,000
- SAM = 100,000 × ₦10,000/year = **₦1 billion ($690k)**

**Serviceable Obtainable Market (SOM)** (Year 1):
- Capture 2% of SAM = 2,000 users
- SOM = 2,000 × ₦10,000/year = **₦20 million ($13,800)**

**Revenue Model**:
- **Tier 1** (Free): 1 quick analysis/month → Acquisition funnel
- **Tier 2** (₦500/debate): Risk assessment only → Occasional users
- **Tier 3** (₦2,000/debate): Full committee review → Power users
- **Subscription** (₦15,000/month): Unlimited Tier 3 → Fund managers

### Competitive Landscape

| Player | Strength | Weakness | AlphaCouncil Edge |
|--------|----------|----------|-------------------|
| **Bloomberg Terminal** | Comprehensive global data | $24,000/year, overkill for retail | ₦2,000/analysis, Nigeria-focused |
| **ChatGPT/Claude** | Fast, conversational | Shallow, no citations, no debate | Multi-agent adversarial debate |
| **Nigerian Brokers** | Local expertise | Slow (1-2 days), promotional bias | 3-min turnaround, neutral AI |
| **Morningstar** | Strong US coverage | Minimal NSE coverage | Built for Nigerian stocks first |
| **Seeking Alpha** | Community insights | Human bias, no systematic rigor | AI agents with forced bear case |

**Sustainable Competitive Advantage**:
1. **Data moat**: Curated Nigerian 10-K corpus (competitors lack this)
2. **Multi-agent architecture**: Patent-pending debate orchestration
3. **Network effects**: More debates → better calibration → higher trust

---

## 13. Document Corpus Strategy: What Gets Embedded Per Company

### The Document Value Hierarchy

For AlphaCouncil's RAG system to deliver verifiable, cited analysis, we need a **curated corpus** of financial documents per tracked company. Not all documents are equally valuable—some provide critical data points, others provide context.

### Tier 1: Must-Have Documents (Core Financial Data)

#### 1. Audited Annual Financial Statements (Last 3 Years)

**What's Included**:
- Complete Income Statement
- Balance Sheet
- Cash Flow Statement
- Notes to Financial Statements (accounting policies, debt schedules, segment breakdown)
- Management Discussion & Analysis (MD&A)
- Auditor's Report

**Why This is Tier 1**:
```python
# Without this, agents say:
"Dangote Cement has strong fundamentals." ❌

# With this embedded, agents say:
"Revenue grew from ₦1.8T (FY2023) to ₦2.1T (FY2025) [REF:1], 
driven by 23% volume growth in cement sales. Gross margin 
expanded from 42.3% to 45.1% [REF:2], while debt-to-equity 
increased to 1.8 [REF:3]." ✅
```

**Data Characteristics**:
- **Document size**: 100-150 pages per annual report
- **Chunks per document**: ~200-300 chunks (1000-char chunks with 200-char overlap)
- **Storage per year**: ~500KB per PDF
- **Total per company**: 3 years × 500KB = **1.5MB**

**Where to Obtain**:
- **Primary source**: Company Investor Relations page (e.g., dangotecement.com/investor-relations)
- **Fallback**: Nigerian Exchange Group (NGX) company filings portal
- **Format**: Usually PDF (may require OCR for scanned documents)

**Ingestion Process**:
```python
# Example ingestion for Dangote Cement
files = [
    "DANGCEM_Annual_Report_FY2023.pdf",
    "DANGCEM_Annual_Report_FY2024.pdf", 
    "DANGCEM_Annual_Report_FY2025.pdf"
]

for pdf_path in files:
    chunks = ingest_10k_filing(
        pdf_path=pdf_path,
        ticker="DANGCEM",
        filing_year=extract_year(pdf_path)
    )
    
    embeddings = generate_embeddings(chunks)
    store_chunks_in_db(embeddings, conn)
    
    print(f"✅ Ingested {len(chunks)} chunks from {pdf_path}")
```

#### 2. Quarterly Unaudited Results (Last 8 Quarters = 2 Years)

**What's Included**:
- Q1, Q2, Q3 quarterly earnings reports (Q4 is captured in annual report)
- Revenue, profit, EPS updates
- Segment performance breakdown
- Key operational metrics (customer growth, production volumes, etc.)
- Management commentary on quarterly performance

**Why This is Critical**:
- **Trend detection**: Spot margin compression or revenue acceleration quarter-by-quarter
- **Seasonality analysis**: Q4 cement demand spikes due to dry season construction
- **Forward guidance**: Management's outlook statements for coming quarters

**Data Characteristics**:
- **Document size**: 20-40 pages per quarterly report
- **Chunks per document**: ~50-100 chunks
- **Total per company**: 8 quarters × 100 chunks = **800 chunks** (~1.2MB)

**Example Agent Use**:
```python
# Fundamental Analyst queries:
retrieve_sec_filings("DANGCEM", "quarterly revenue trends last 2 years")

# Returns:
[REF:4] "Q1 2024 revenue: ₦487B (+12% YoY), Q2 2024: ₦521B (+15% YoY), 
Q3 2024: ₦539B (+18% YoY), showing accelerating growth momentum."
```

#### 3. Earnings Call Transcripts (If Available)

**What's Included**:
- CEO/CFO prepared remarks
- Q&A session with analysts
- Forward-looking statements on strategy, capex, guidance

**Why This is Gold**:
```python
[REF:5] "CFO stated during Q3 2025 earnings call: 
'We expect CAPEX for FY2026 to be in the range of ₦180-200B, 
focused on Senegal plant expansion and energy cost optimization. 
We've secured long-term gas supply contracts that should reduce 
energy costs by 15% starting Q2 2026.'"
```

**Reality Check for Nigeria**: 
- Most Nigerian companies **do not publish call transcripts**
- When available (MTN Nigeria, Dangote Cement occasionally): extremely high value
- **Status**: OPTIONAL for MVP, HIGH PRIORITY if accessible

**Data Characteristics**:
- **Document size**: 15-30 pages per transcript
- **Chunks**: ~50-100 per transcript
- **Availability**: <20% of NSE companies publish these

### Tier 2: High-Value Context Documents

#### 4. Investor Presentations / Factsheets

**What's Included**:
- Slide decks used at investor conferences
- Business model overview
- Market position & competitive advantages
- Strategic initiatives (new product launches, market expansion)
- 5-year financial highlights in visual format

**Why This Matters**:
- **Management's narrative**: How they *want* to be perceived
- **Forward-looking strategy**: M&A targets, new markets, innovation pipeline
- **Key metrics tracking**: Which KPIs management considers most important

**Data Characteristics**:
- **Document size**: 15-25 slides per presentation
- **Chunks**: ~30-50 per presentation
- **Frequency**: 3-5 presentations per year (annual, quarterly investor days)
- **Total per company**: ~200 chunks (~400KB)

**Example Citations**:
```python
[REF:6] "Management's FY2025 Investor Day presentation shows 
target of 30% market share in East Africa by 2027, up from 
current 18% [REF:6, Slide 12]."
```

#### 5. Annual Reports (Non-Financial Sections)

**What's Included**:
- Chairman's statement (strategic overview)
- Corporate governance report (board composition, executive compensation)
- **Risk factors disclosure** (key risks to business)
- Industry overview & market trends
- Sustainability/ESG initiatives

**Why This is High-Value**:
```python
[REF:7] "Management identified three principal risks in FY2025 Annual Report:
1) Naira depreciation impact on USD-denominated debt (40% of total debt)
2) Rising energy costs (diesel accounts for 35% of production costs)
3) Regulatory risk: potential cement import tariff reductions
[REF:7, Risk Factors section, p.87]"
```

**Data Characteristics**:
- **Chunks**: ~100-150 per annual report (non-financial sections)
- **Storage**: ~800KB for 3 years of reports

### Tier 3: Contextual Intelligence (Market & Sentiment)

#### 6. Recent Financial News (Last 90 Days)

**What's Included**:
- News articles from Nigerian financial media:
  - Nairametrics
  - BusinessDay Nigeria
  - Punch Business
  - Vanguard Business
  - The Guardian Nigeria
- Company press releases
- Material event announcements

**Why This Matters**:
- **Sentiment gauge**: Market perception shifts (bullish/bearish turns)
- **Event detection**: CEO changes, M&A rumors, regulatory actions, strikes
- **Peer comparison**: "Access Bank gained deposit market share while GTBank..."

**Data Characteristics**:
- **Articles per company**: ~30 articles over 90 days (1 every 3 days for top stocks)
- **Chunks per article**: 5-10 chunks (short articles)
- **Total**: ~200 chunks per company (~400KB)
- **Refresh frequency**: **Daily scraping** (news is time-sensitive)

**Implementation**:
```python
# Daily cron job
@daily_task
def refresh_news_corpus():
    for ticker in TRACKED_TICKERS:
        articles = scrape_recent_news(ticker, days_back=90)
        
        # Embed and store
        for article in articles:
            chunks = chunk_text(article['text'])
            embeddings = generate_embeddings(chunks)
            store_chunks_in_db(embeddings, conn)
        
        print(f"✅ Refreshed {len(articles)} news articles for {ticker}")
```

#### 7. Regulatory Filings with NGX

**What's Included**:
- Material event notifications (acquisitions, disposals, director changes)
- Dividend declarations
- Share buyback programs
- Related party transactions disclosure
- Profit warnings / trading updates

**Where to Get**: Nigerian Exchange Group (NGX) disclosures portal

**Why This Matters**: **Early signals** of corporate actions before they hit mainstream news

**Data Characteristics**:
- **Filings per company per year**: ~10-20
- **Chunks**: ~100 total per company
- **Storage**: ~200KB

#### 8. Analyst Reports (If Accessible)

**What's Included**:
- Equity research reports from Nigerian brokerages:
  - Stanbic IBTC
  - Chapel Hill Denham
  - Cordros Capital
  - Vetiva Capital
- Target price estimates
- Buy/Sell/Hold recommendations
- Detailed financial models

**Reality Check**: 
- Most analyst reports are **behind paywalls** or only available to brokerage clients
- **Status**: SKIP for MVP unless you have access

**If Accessible**:
- **Chunks**: ~100-200 per report
- **Value**: ⭐⭐⭐⭐ (professional analysis benchmarks)

### Tier 4: Optional Enrichment (Industry Context)

#### 9. Industry & Sector Reports

**What's Included**:
- Nigerian cement industry outlook (for DANGCEM, BUACEMENT)
- Banking sector analysis (for ACCESS, GTCO, ZENITHBANK)
- Telecom market dynamics (for MTNN, AIRTELAFRI)
- Oil & Gas sector trends (for SEPLAT, OANDO)

**Sources**:
- Nigerian Bureau of Statistics (nigerianstat.gov.ng)
- Central Bank of Nigeria (CBN) sector reports
- African Development Bank industry reports
- PwC Nigeria sector surveys

**Why This Adds Value**:
- **Benchmark competitors**: "Dangote Cement's 45% margin vs industry avg 38%"
- **Sector tailwinds/headwinds**: "CBN banking recapitalization requirements"
- **Market size estimation**: "Nigerian cement market = 28M tonnes/year"

**Data Characteristics**:
- **Reports per sector**: 3-5 major reports per year
- **Chunks**: ~200 per report
- **Coverage**: Share across 5-10 companies in same sector

### Complete Corpus Size Per Company

| Document Type | Count | Chunks | Storage | Priority |
|---------------|-------|--------|---------|----------|
| **Annual Reports (3 years)** | 3 | 750 | 1.5MB | ⭐⭐⭐⭐⭐ MUST HAVE |
| **Quarterly Results (8 qtrs)** | 8 | 600 | 1.2MB | ⭐⭐⭐⭐⭐ MUST HAVE |
| **Investor Presentations** | 5 | 200 | 400KB | ⭐⭐⭐⭐ HIGH |
| **Annual Report (non-financial)** | 3 | 400 | 800KB | ⭐⭐⭐⭐ HIGH |
| **News articles (90 days)** | 30 | 200 | 400KB | ⭐⭐⭐ MEDIUM |
| **Regulatory filings** | 10 | 100 | 200KB | ⭐⭐ LOW |
| **Earnings call transcripts** | 4 | 200 | 400KB | ⭐⭐⭐⭐⭐ IF AVAILABLE |
| **Analyst reports** | 3 | 300 | 600KB | ⭐⭐⭐⭐ IF ACCESSIBLE |
| **TOTAL (Full Production)** | **~60** | **~2,250** | **~4.5MB** | |

**For 10 companies**: 10 × 2,250 = **22,500 chunks** (~45MB embeddings storage)

**For 50 companies** (NSE top 50): 50 × 2,250 = **112,500 chunks** (~225MB embeddings)

### Minimum Viable Corpus (MVP Strategy)

To prove the concept **quickly without overwhelming data collection**, start with:

#### Phase 1: Top 5 Companies Only

**Company Selection**:
1. DANGCEM (Dangote Cement) - Cement sector
2. ACCESS (Access Holdings) - Banking
3. MTNN (MTN Nigeria) - Telecom
4. BUACEMENT (BUA Cement) - Cement competitor
5. GTCO (Guaranty Trust Holding) - Banking

**Document Set Per Company**:
1. ✅ **Latest Annual Report** (FY2025) — 1 PDF
2. ✅ **Latest 2 Quarterly Results** (Q3 2025, Q2 2025) — 2 PDFs
3. ✅ **Last 20 News Articles** — Scraped from Nairametrics

**Total MVP Corpus**:
- **Documents**: 3-5 docs × 5 companies = **15-25 PDFs**
- **Chunks**: ~500 per company × 5 = **2,500 chunks**
- **Storage**: ~1MB per company × 5 = **5MB total**
- **Ingestion time**: ~15 minutes one-time setup

**This is enough to demonstrate**:
- ✅ Agents cite specific revenue numbers from annual reports
- ✅ Agents track quarterly trends
- ✅ Agents reference recent news sentiment
- ✅ Citations are verifiable (click [REF:n] → see source)

#### Phase 2: Expand to 3-Year History (Post-MVP)

Once MVP proves valuable:
- Add FY2023, FY2024 annual reports (backfill historical data)
- Add all 8 quarterly results (spot trends over 2 years)
- Expand news corpus to 90 days

**New corpus**: ~2,250 chunks per company

#### Phase 3: Scale to Top 20 NSE Stocks

Expand coverage to:
- Top 10 banks (ACCESS, GTCO, UBA, ZENITHBANK, etc.)
- Top 5 industrials (DANGCEM, BUACEMENT, FLOURMILL, NESTLE)
- Top 5 others (MTNN, SEPLAT, AIRTELAFRI)

**Total**: 20 companies × 2,250 chunks = **45,000 chunks** (~90MB)

### Data Collection Workflow

#### Automated Pipeline

```python
# File: scripts/ingest_company_documents.py

COMPANIES = {
    "DANGCEM": {
        "name": "Dangote Cement Plc",
        "ir_url": "https://www.dangotecement.com/investor-relations/",
        "nse_code": "DANGCEM",
        "sector": "Industrials"
    },
    "ACCESS": {
        "name": "Access Holdings Plc",
        "ir_url": "https://www.accessbankplc.com/investor-relations/",
        "nse_code": "ACCESSCORP",
        "sector": "Banking"
    },
    # ... more companies
}

def ingest_company_corpus(ticker: str, phase: str = "mvp"):
    """
    Ingests all documents for a company based on phase.
    
    Args:
        ticker: Stock ticker (e.g., 'DANGCEM')
        phase: 'mvp' (latest only) | 'full' (3-year history)
    """
    company = COMPANIES[ticker]
    
    # Step 1: Scrape Investor Relations page
    annual_reports = scrape_ir_page(company['ir_url'], doc_type='annual_report')
    quarterly_results = scrape_ir_page(company['ir_url'], doc_type='quarterly')
    
    if phase == "mvp":
        annual_reports = annual_reports[:1]  # Latest only
        quarterly_results = quarterly_results[:2]  # Latest 2 quarters
    else:
        annual_reports = annual_reports[:3]  # Last 3 years
        quarterly_results = quarterly_results[:8]  # Last 8 quarters
    
    # Step 2: Download PDFs
    for report in annual_reports + quarterly_results:
        pdf_path = download_pdf(report['url'], ticker)
        
        # Step 3: Extract text + chunk + embed
        chunks = ingest_10k_filing(pdf_path, ticker, report['fiscal_year'])
        embeddings = generate_embeddings(chunks)
        store_chunks_in_db(embeddings, conn)
        
        print(f"✅ Ingested {len(chunks)} chunks from {report['title']}")
    
    # Step 4: Scrape news
    articles = scrape_recent_news(ticker, company['name'], days_back=90)
    for article in articles:
        chunks = chunk_text(article['text'])
        embeddings = generate_embeddings(chunks)
        store_chunks_in_db(embeddings, conn)
    
    print(f"✅ Ingested {len(articles)} news articles for {ticker}")
    
    return {
        'ticker': ticker,
        'total_chunks': len(chunks),
        'documents': len(annual_reports) + len(quarterly_results),
        'news_articles': len(articles)
    }

# Run for all MVP companies
for ticker in ["DANGCEM", "ACCESS", "MTNN", "BUACEMENT", "GTCO"]:
    result = ingest_company_corpus(ticker, phase="mvp")
    print(f"\n📊 {ticker}: {result['total_chunks']} chunks ingested")
```

### Quality Assurance: What Makes a Good Corpus?

After ingestion, validate quality:

```python
def validate_corpus_quality(ticker: str):
    """
    Checks if the embedded corpus is sufficient for agent citations.
    """
    test_queries = [
        "revenue growth last 3 years",
        "debt to equity ratio",
        "management discussion of risks",
        "dividend policy",
        "recent news sentiment"
    ]
    
    for query in test_queries:
        results = retrieve_sec_filings(ticker, query, top_k=3)
        
        if not results:
            print(f"❌ {ticker}: No results for '{query}'")
        else:
            print(f"✅ {ticker}: Found {len(results)} results for '{query}'")
            print(f"   Top result: {results[0]['text'][:100]}...")
```

**Quality Criteria**:
- ✅ Every test query returns at least 3 relevant chunks
- ✅ Chunks contain specific numbers (not just generic text)
- ✅ Citations trace back to exact document + page number
- ✅ Coverage spans at least 2 years of financial data

---

## 14. Security, Compliance & Risk Mitigation

### Legal Disclaimer: AlphaCouncil is NOT a Registered Investment Advisor

**Critical Legal Position**: AlphaCouncil provides **decision support tools**, not investment advice. This distinction must be clear in:

1. **User-facing disclaimers** (on every page, every output)
2. **Terms of Service**
3. **API responses** (footer in every debate result)
4. **Marketing materials**

**Standard Disclaimer Text**:
```
⚠️ IMPORTANT DISCLAIMER

AlphaCouncil is an AI-powered research tool that provides information and analysis 
for educational purposes only. It is NOT a registered investment advisor and does 
NOT provide personalized investment advice.

All analysis, recommendations, and verdicts generated by AlphaCouncil are based on 
AI agents processing publicly available data and should NOT be considered as:
- Professional financial advice
- A recommendation to buy, sell, or hold any security
- A guarantee of future performance
- A substitute for your own research and due diligence

You alone are responsible for your investment decisions. Past performance does not 
guarantee future results. Investing involves risk, including possible loss of principal.

Consult a qualified financial advisor before making investment decisions.
```

This disclaimer must appear:
- ✅ On the homepage (above fold)
- ✅ In the debate input form (must be acknowledged before submitting)
- ✅ At the top of every investment memo (PDF export)
- ✅ In the JSON API response (dedicated `disclaimer` field)
- ✅ In the footer of every page

### Security Architecture

#### Authentication & Authorization

**User Authentication**:
```python
# JWT-based authentication with secure token handling

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 256-bit random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Creates a JWT access token for authenticated users.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates JWT token and returns current user.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Fetch user from database
        user = db.users.find_one({"user_id": user_id})
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

**Authorization Levels**:
```python
# Rate limiting based on subscription tier

RATE_LIMITS = {
    "free": {
        "debates_per_month": 5,
        "tier_3_allowed": False,
        "max_companies_tracked": 5
    },
    "basic": {
        "debates_per_month": 50,
        "tier_3_allowed": True,
        "max_companies_tracked": 20
    },
    "pro": {
        "debates_per_month": -1,  # Unlimited
        "tier_3_allowed": True,
        "max_companies_tracked": -1  # Unlimited
    }
}

def check_rate_limit(user: dict, tier: int) -> bool:
    """
    Checks if user has remaining quota for debates.
    """
    limits = RATE_LIMITS[user['subscription_tier']]
    
    # Check monthly debate limit
    if limits['debates_per_month'] != -1:
        if user['debates_run_this_month'] >= limits['debates_per_month']:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly debate limit reached ({limits['debates_per_month']}). Upgrade to continue."
            )
    
    # Check tier access
    if tier == 3 and not limits['tier_3_allowed']:
        raise HTTPException(
            status_code=403,
            detail="Tier 3 debates require Basic or Pro subscription."
        )
    
    return True
```

#### API Security

**Rate Limiting** (prevent abuse):
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Redis-backed rate limiting
@app.post("/api/v1/debates")
@limiter.limit("10/minute")  # Max 10 debate requests per minute
async def create_debate(
    request: DebateRequest,
    user: dict = Depends(get_current_user)
):
    # ... debate creation logic
```

**Input Validation** (prevent injection attacks):
```python
from pydantic import BaseModel, validator, Field

class DebateRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, regex="^[A-Z0-9]+$")
    company_name: str | None = Field(None, max_length=200)
    user_thesis: str = Field(..., min_length=10, max_length=5000)
    capital_to_deploy: float = Field(..., gt=0, le=1_000_000_000)  # Max ₦1B
    risk_tolerance: str = Field(..., regex="^(conservative|moderate|aggressive)$")
    tier: int = Field(..., ge=1, le=3)
    
    @validator('user_thesis')
    def sanitize_thesis(cls, v):
        """
        Prevents prompt injection in user thesis.
        """
        # Block attempts to inject LLM instructions
        forbidden_phrases = [
            "ignore previous instructions",
            "system:",
            "assistant:",
            "<|im_start|>",
            "you are now",
            "forget everything"
        ]
        
        v_lower = v.lower()
        for phrase in forbidden_phrases:
            if phrase in v_lower:
                raise ValueError(f"Invalid input: contains forbidden phrase")
        
        return v
```

**SQL Injection Prevention**:
```python
# Use parameterized queries (psycopg2 automatically escapes)

def get_user_debates(user_id: str, limit: int):
    """
    Safe query - user_id is parameterized, not concatenated.
    """
    cursor.execute(
        "SELECT * FROM debates WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit)
    )
    
    return cursor.fetchall()
```

#### Data Privacy & PII Protection

**What AlphaCouncil Stores**:
- ✅ User email, hashed password (bcrypt with salt)
- ✅ Debate history (ticker, thesis, verdict)
- ✅ Financial documents (public data only - 10-Ks, news articles)

**What AlphaCouncil Does NOT Store**:
- ❌ Actual portfolio holdings (we never ask for this)
- ❌ Brokerage account credentials
- ❌ Bank account details
- ❌ Payment card numbers (Stripe handles payments, we store only customer ID)

**Data Retention Policy**:
```python
# Auto-delete old debates after 2 years

@monthly_task
def cleanup_old_debates():
    """
    Deletes debates older than 2 years to comply with data minimization.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=730)
    
    result = db.debates.delete_many({
        'created_at': {'$lt': cutoff_date}
    })
    
    print(f"🗑️ Deleted {result.deleted_count} debates older than 2 years")
```

**GDPR Compliance** (Right to be Forgotten):
```python
@app.delete("/api/v1/user/delete")
async def delete_user_account(user: dict = Depends(get_current_user)):
    """
    Permanently deletes user account and all associated data.
    """
    user_id = user['user_id']
    
    # Delete all user data
    db.debates.delete_many({'user_id': user_id})
    db.users.delete_one({'user_id': user_id})
    
    # Cancel Stripe subscription
    if user.get('stripe_customer_id'):
        stripe.Customer.delete(user['stripe_customer_id'])
    
    return {
        'message': 'Account and all associated data permanently deleted',
        'user_id': user_id
    }
```

#### Secrets Management

**Environment Variables** (.env file, never committed to Git):
```bash
# .env (add to .gitignore)

# Database
DATABASE_URL=postgresql://user:pass@host:5432/alphacouncil
REDIS_URL=redis://localhost:6379/0

# API Keys (encrypted at rest)
NEWS_API_KEY=your_newsapi_key
FMP_API_KEY=your_financialmodelingprep_key
GROQ_API_KEY=your_groq_key

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your_256_bit_random_secret

# Stripe (payment processing)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# SendGrid (email notifications)
SENDGRID_API_KEY=SG...

# Environment
ENVIRONMENT=production  # or 'development', 'staging'
```

**Secure Key Storage** (use environment-specific secrets):
```python
import os
from cryptography.fernet import Fernet

# Encrypt sensitive config at rest
def encrypt_api_key(api_key: str) -> bytes:
    """
    Encrypts API keys before storing in database.
    """
    key = os.getenv("ENCRYPTION_KEY").encode()
    f = Fernet(key)
    return f.encrypt(api_key.encode())

def decrypt_api_key(encrypted_key: bytes) -> str:
    """
    Decrypts API keys when needed.
    """
    key = os.getenv("ENCRYPTION_KEY").encode()
    f = Fernet(key)
    return f.decrypt(encrypted_key).decode()
```

### Nigerian Regulatory Compliance

#### Securities and Exchange Commission (SEC) Nigeria

**Regulatory Position**:
- AlphaCouncil is **not** providing investment advice (no SEC registration required)
- AlphaCouncil is **not** executing trades (no brokerage license required)
- AlphaCouncil **is** providing information/research tools (permissible)

**Compliance Requirements**:
1. ✅ **Prominent disclaimers** (already covered above)
2. ✅ **No personalized recommendations** (debate is generated, not human-written)
3. ✅ **Transparent methodology** (explain how agents work)
4. ✅ **No performance guarantees** (every output includes uncertainty/confidence scores)

**Sample "About Our Methodology" Page**:
```markdown
## How AlphaCouncil Works

AlphaCouncil uses artificial intelligence (AI) agents to analyze publicly available 
financial data. Here's what happens when you run a debate:

1. **Document Retrieval**: AI agents search financial filings (annual reports, 
   quarterly results) for relevant information about your chosen stock.

2. **Multi-Agent Debate**: Three specialized AI agents debate the investment case:
   - Fundamental Analyst builds the bull case
   - Quantitative Auditor builds the bear case  
   - Risk & Macro Strategist provides economic context

3. **Synthesis**: An AI arbitrator weighs the arguments and produces a verdict 
   with a confidence score (e.g., 68% confidence).

**Important Limitations**:
- AI agents can make mistakes or miss important information
- Past financial data does not guarantee future performance
- Confidence scores are estimates, not certainties
- The system cannot predict unforeseen events (black swans)

**This is NOT financial advice**. AlphaCouncil provides research tools to help you 
make informed decisions, but you alone are responsible for your investments.
```

#### Data Protection Act (Nigeria)

**User Consent**:
```html
<!-- Privacy Policy Acceptance (on signup) -->
<form action="/api/v1/auth/register" method="POST">
  <input type="email" name="email" required>
  <input type="password" name="password" required>
  
  <label>
    <input type="checkbox" name="accept_privacy_policy" required>
    I have read and accept the 
    <a href="/privacy-policy" target="_blank">Privacy Policy</a>
  </label>
  
  <label>
    <input type="checkbox" name="accept_terms" required>
    I agree to the <a href="/terms" target="_blank">Terms of Service</a>
  </label>
  
  <button type="submit">Create Account</button>
</form>
```

**Privacy Policy Key Points** (must include):
1. What data we collect (email, debate history)
2. How we use it (service delivery, analytics)
3. Who we share it with (nobody - debates are private)
4. How users can delete their data (account deletion API)
5. How we secure data (encryption, access controls)

### Risk Mitigation Strategies

#### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **LLM Hallucination** | High | High | - Force citation of sources (RAG) <br> - Manual spot-checks of 50 debates <br> - User feedback mechanism ("Report incorrect citation") |
| **10-K Data Unavailable** | Medium | High | - Fallback to Yahoo Finance/FMP APIs <br> - Manual curation for top 20 NSE stocks <br> - Graceful degradation (warn user if limited data) |
| **API Rate Limits (Groq)** | Medium | Medium | - Exponential backoff retry logic <br> - Paid tier as backup (Claude Haiku) <br> - Queue system for demand spikes |
| **Debate Loops (Agents Don't Converge)** | Medium | Medium | - Hard cap at 5 turns <br> - Moderator forced exit logic <br> - Timeout after 10 minutes |
| **Database Failure** | Low | High | - Automated daily backups (Supabase) <br> - Hot standby replica <br> - Point-in-time recovery (7 days) |
| **DDoS Attack** | Low | Medium | - Cloudflare DDoS protection <br> - Rate limiting (100 req/min per IP) <br> - Auto-scaling (Railway) |

#### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Low User Trust in AI** | High | High | - Transparent methodology page <br> - Show debate transcript (not just verdict) <br> - Honest confidence scores (65% ≠ 95%) <br> - User testimonials / case studies |
| **Regulatory Crackdown** | Low | High | - Legal disclaimer on every page <br> - Consult Nigerian securities lawyer <br> - Monitor SEC Nigeria guidance <br> - Join fintech associations |
| **Competitors (Bigger Players)** | Medium | Medium | - Focus on Nigerian market (niche) <br> - Build data moat (curated 10-K corpus) <br> - Patent multi-agent debate architecture |
| **Data Quality (NSE Filings)** | High | Medium | - Manual curation for top 20 stocks <br> - Community flagging of errors <br> - Partnerships with data vendors |

---

## 15. Testing Strategy & Quality Assurance

### Testing Pyramid for AlphaCouncil

```
           /\
          /  \           E2E Tests (10%)
         /----\          - Full debate flows
        /      \         - User journeys
       /--------\        
      /          \       Integration Tests (30%)
     /------------\      - Agent + tools + LangGraph
    /              \     - RAG retrieval accuracy
   /----------------\    - API endpoints
  /                  \   
 /--------------------\  Unit Tests (60%)
/______________________\ - Tool functions
                        - Prompt templates
                        - Data processing
```

### Unit Tests (60% of test coverage)

#### Tool Function Tests

```python
# tests/tools/test_financial_ratios.py

import pytest
from unittest.mock import Mock, patch
from tools.financial_ratios import fetch_financial_ratios

def test_fetch_financial_ratios_success():
    """
    Tests that fetch_financial_ratios returns correct data for valid ticker.
    """
    result = fetch_financial_ratios("DANGCEM")
    data = json.loads(result)
    
    assert data['ticker'] == "DANGCEM"
    assert data['data_source'] in ['yahoo_finance', 'financial_modeling_prep']
    assert 'pe_ratio' in data['ratios']
    assert 'debt_to_equity' in data['ratios']

def test_fetch_financial_ratios_invalid_ticker():
    """
    Tests that invalid ticker returns graceful error.
    """
    result = fetch_financial_ratios("INVALID123")
    data = json.loads(result)
    
    assert 'error' in data or len(data['warnings']) > 0

@patch('yfinance.Ticker')
def test_fetch_financial_ratios_api_failure(mock_ticker):
    """
    Tests fallback behavior when Yahoo Finance API fails.
    """
    mock_ticker.side_effect = Exception("API timeout")
    
    result = fetch_financial_ratios("DANGCEM")
    data = json.loads(result)
    
    # Should fallback to FMP or return error
    assert data['data_source'] == 'financial_modeling_prep' or 'error' in data
```

#### DCF Model Tests

```python
# tests/tools/test_dcf_model.py

def test_dcf_basic_calculation():
    """
    Tests DCF model with known inputs produces expected output.
    """
    result = run_dcf_model(
        free_cash_flow=1000,  # ₦1B FCF
        growth_rate=0.10,     # 10% growth
        terminal_growth=0.03, # 3% terminal
        wacc=0.12,            # 12% WACC
        shares_outstanding=100,
        years=5
    )
    
    data = json.loads(result)
    
    # Year 1 FCF should be 1000 * 1.1 = 1100
    assert abs(data['projected_fcf'][0] - 1100) < 1
    
    # PV should be less than sum of nominal FCF (discounting)
    assert data['pv_cash_flows'] < sum(data['projected_fcf'])
    
    # Intrinsic value should be reasonable (not negative, not absurdly high)
    assert 0 < data['intrinsic_value_per_share'] < 1000

def test_dcf_edge_cases():
    """
    Tests DCF handles edge cases without crashing.
    """
    # Zero FCF
    result = run_dcf_model(0, 0.10, 0.03, 0.12, 100)
    assert json.loads(result)['intrinsic_value_per_share'] == 0
    
    # WACC > growth rate (required for Gordon Growth Model)
    with pytest.raises(ValueError):
        run_dcf_model(1000, 0.15, 0.20, 0.12, 100)  # terminal_growth > WACC
```

#### RAG Retrieval Tests

```python
# tests/rag/test_retrieval.py

def test_retrieve_sec_filings_finds_revenue():
    """
    Tests that RAG finds revenue data when queried.
    """
    # Assuming DANGCEM corpus is already ingested in test DB
    result = retrieve_sec_filings("DANGCEM", "revenue growth")
    
    assert "[REF:1]" in result
    assert "revenue" in result.lower()
    assert "₦" in result or "NGN" in result  # Currency mention

def test_retrieve_sec_filings_empty_corpus():
    """
    Tests graceful handling when no documents exist for ticker.
    """
    result = retrieve_sec_filings("NOTEXIST", "revenue")
    data = json.loads(result)
    
    assert 'error' in data
    assert 'no financial documents found' in data['error'].lower()

def test_embedding_generation_consistency():
    """
    Tests that same text produces same embedding (deterministic).
    """
    text = "Revenue grew 18.7% year over year"
    
    emb1 = embedding_model.encode([text])[0]
    emb2 = embedding_model.encode([text])[0]
    
    # Cosine similarity should be 1.0 (identical)
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    assert similarity > 0.999
```

### Integration Tests (30% of coverage)

#### Agent + Tools Integration

```python
# tests/integration/test_agent_tools.py

def test_fundamental_analyst_cites_sources():
    """
    Tests that Fundamental Analyst agent uses tools and cites [REF:n].
    """
    # Mock LLM to avoid API costs in tests
    with patch('langchain_groq.ChatGroq') as mock_llm:
        mock_llm.return_value.invoke.return_value = Mock(
            content="Revenue grew 18.7% [REF:1]"
        )
        
        state = {
            'ticker': 'DANGCEM',
            'messages': [],
            # ... minimal state
        }
        
        result = fundamental_analyst_node(state)
        
        # Agent should have made tool calls
        assert len(state['messages']) > 0
        
        # Agent should cite sources
        assert '[REF:' in state['messages'][-1]['content']
```

#### Full Debate Flow Test

```python
# tests/integration/test_debate_flow.py

@pytest.mark.slow  # Mark as slow test (runs actual LLM calls)
def test_end_to_end_debate():
    """
    Runs a full debate for DANGCEM (uses real APIs, takes 2-3 min).
    """
    initial_state = {
        'ticker': 'DANGCEM',
        'company_name': 'Dangote Cement Plc',
        'user_thesis': 'Infrastructure boom will drive cement demand',
        'capital_to_deploy': 5000000,
        'risk_tolerance': 'moderate',
        'messages': [],
        'current_turn': 0,
        'max_turns': 5,
        'debate_complete': False
    }
    
    graph = build_debate_graph()
    final_state = graph.invoke(initial_state)
    
    # Verify debate completed
    assert final_state['debate_complete'] == True
    
    # Verify all agents spoke
    agent_roles = [msg['agent_role'] for msg in final_state['messages']]
    assert 'fundamental_analyst' in agent_roles
    assert 'quantitative_auditor' in agent_roles
    assert 'risk_strategist' in agent_roles
    
    # Verify final verdict exists
    assert 'final_verdict' in final_state
    assert final_state['final_verdict']['verdict'] in [
        'STRONG_BUY', 'BUY', 'CONDITIONAL_BUY', 'HOLD', 'AVOID'
    ]
    
    # Verify confidence is reasonable
    assert 0.4 <= final_state['final_verdict']['confidence'] <= 0.95
```

#### API Endpoint Tests

```python
# tests/integration/test_api_endpoints.py

from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_debate_endpoint():
    """
    Tests POST /api/v1/debates endpoint.
    """
    # Mock authentication
    headers = {"Authorization": f"Bearer {get_test_token()}"}
    
    response = client.post(
        "/api/v1/debates",
        json={
            "ticker": "DANGCEM",
            "user_thesis": "Infrastructure boom",
            "capital_to_deploy": 5000000,
            "risk_tolerance": "moderate",
            "tier": 3
        },
        headers=headers
    )
    
    assert response.status_code == 202  # Accepted (async)
    data = response.json()
    
    assert 'debate_id' in data
    assert data['status'] == 'running'
    assert 'websocket_url' in data

def test_get_debate_status():
    """
    Tests GET /api/v1/debates/{debate_id}/status endpoint.
    """
    # First create a debate
    debate_id = create_test_debate()
    
    # Poll status
    response = client.get(
        f"/api/v1/debates/{debate_id}/status",
        headers={"Authorization": f"Bearer {get_test_token()}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data['debate_id'] == debate_id
    assert data['status'] in ['running', 'debating', 'completed', 'failed']

def test_rate_limiting():
    """
    Tests that free tier users hit rate limit.
    """
    headers = {"Authorization": f"Bearer {get_free_tier_token()}"}
    
    # Make 6 requests (free tier limit is 5/month)
    for i in range(6):
        response = client.post(
            "/api/v1/debates",
            json=get_test_debate_request(),
            headers=headers
        )
        
        if i < 5:
            assert response.status_code == 202
        else:
            assert response.status_code == 429  # Too Many Requests
```

### End-to-End Tests (10% of coverage)

#### User Journey: First Debate

```python
# tests/e2e/test_user_journey.py

@pytest.mark.e2e
def test_new_user_runs_first_debate():
    """
    Simulates a new user signing up and running their first debate.
    """
    # Step 1: Sign up
    response = client.post("/api/v1/auth/register", json={
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    
    assert response.status_code == 201
    user_data = response.json()
    token = user_data['access_token']
    
    # Step 2: Create debate
    response = client.post(
        "/api/v1/debates",
        json={
            "ticker": "DANGCEM",
            "user_thesis": "Strong fundamentals",
            "capital_to_deploy": 5000000,
            "risk_tolerance": "moderate",
            "tier": 1  # Free tier: quick check
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 202
    debate_id = response.json()['debate_id']
    
    # Step 3: Poll until complete (max 5 min)
    for _ in range(60):  # 60 * 5s = 5 min timeout
        response = client.get(
            f"/api/v1/debates/{debate_id}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        status = response.json()['status']
        
        if status == 'completed':
            break
        elif status == 'failed':
            pytest.fail(f"Debate failed: {response.json().get('error')}")
        
        time.sleep(5)
    
    # Step 4: Get full results
    response = client.get(
        f"/api/v1/debates/{debate_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    debate = response.json()
    
    # Verify structure
    assert 'final_verdict' in debate
    assert 'debate_transcript' in debate
    assert len(debate['debate_transcript']) > 0
```

### Quality Metrics & Agent Evaluation

#### Debate Quality Scorecard

After each debate, automatically score:

```python
def evaluate_debate_quality(debate: dict) -> dict:
    """
    Scores a completed debate on multiple quality dimensions.
    """
    scores = {}
    
    # 1. Citation coverage (what % of claims are cited?)
    total_claims = count_claims(debate['debate_transcript'])
    cited_claims = count_citations(debate['debate_transcript'])
    scores['citation_coverage'] = cited_claims / total_claims if total_claims > 0 else 0
    
    # 2. Debate balance (are bull and bear cases similar in length?)
    bull_words = word_count(get_agent_message(debate, 'fundamental_analyst'))
    bear_words = word_count(get_agent_message(debate, 'quantitative_auditor'))
    scores['balance'] = 1 - abs(bull_words - bear_words) / max(bull_words, bear_words)
    
    # 3. Specificity (numeric data vs vague claims)
    numeric_mentions = count_numbers(debate['debate_transcript'])
    scores['specificity'] = min(numeric_mentions / 10, 1.0)  # Target: 10+ numbers
    
    # 4. Coherence (did agents engage with each other's points?)
    rebuttal_score = check_for_rebuttals(debate['debate_transcript'])
    scores['coherence'] = rebuttal_score
    
    # 5. Actionability (does verdict have specific recommendations?)
    verdict = debate['final_verdict']
    has_stop_loss = 'stop_loss' in verdict['recommendation']
    has_allocation = 'allocation_ngn' in verdict['recommendation']
    has_triggers = len(verdict.get('monitoring_triggers', [])) > 0
    scores['actionability'] = (has_stop_loss + has_allocation + has_triggers) / 3
    
    # Overall score (weighted average)
    scores['overall'] = (
        scores['citation_coverage'] * 0.30 +
        scores['balance'] * 0.15 +
        scores['specificity'] * 0.25 +
        scores['coherence'] * 0.15 +
        scores['actionability'] * 0.15
    )
    
    return scores
```

**Quality Thresholds**:
- ✅ **Good debate**: Overall score ≥ 0.75
- ⚠️ **Acceptable debate**: Overall score 0.60-0.74
- ❌ **Poor debate**: Overall score < 0.60 (flag for manual review)

#### Backtesting: Recommendation Accuracy

Track debate verdicts against actual stock performance:

```python
@monthly_task
def backtest_debate_accuracy():
    """
    Measures how well AlphaCouncil's verdicts predicted actual outcomes.
    """
    # Get debates from 6 months ago
    cutoff_date = datetime.utcnow() - timedelta(days=180)
    debates = db.debates.find({
        'completed_at': {'$lt': cutoff_date},
        'status': 'completed'
    })
    
    results = []
    
    for debate in debates:
        ticker = debate['ticker']
        verdict = debate['final_verdict']['verdict']
        entry_price = debate['final_verdict']['recommendation']['current_price']
        
        # Get actual price 6 months later
        actual_price = get_historical_price(ticker, cutoff_date + timedelta(days=180))
        
        if actual_price is None:
            continue
        
        actual_return = (actual_price - entry_price) / entry_price
        
        # Score verdict accuracy
        correct = False
        if verdict in ['STRONG_BUY', 'BUY'] and actual_return > 0:
            correct = True
        elif verdict == 'CONDITIONAL_BUY' and -0.05 < actual_return < 0.20:
            correct = True  # Modest gains acceptable
        elif verdict == 'HOLD' and -0.10 < actual_return < 0.10:
            correct = True
        elif verdict == 'AVOID' and actual_return < 0:
            correct = True
        
        results.append({
            'debate_id': debate['debate_id'],
            'ticker': ticker,
            'verdict': verdict,
            'predicted_direction': 'positive' if verdict in ['STRONG_BUY', 'BUY', 'CONDITIONAL_BUY'] else 'negative',
            'actual_return': actual_return,
            'correct': correct
        })
    
    accuracy = sum(r['correct'] for r in results) / len(results) if results else 0
    
    print(f"📊 Backtesting Results:")
    print(f"   Debates analyzed: {len(results)}")
    print(f"   Accuracy: {accuracy:.1%}")
    
    # Save to analytics
    db.analytics.insert_one({
        'metric': 'debate_accuracy_6mo',
        'value': accuracy,
        'sample_size': len(results),
        'date': datetime.utcnow()
    })
    
    return accuracy
```

**Target Accuracy**:
- **Minimum acceptable**: 55% (better than random)
- **Good performance**: 60-65%
- **Excellent performance**: >70%

*Note: Even professional analysts achieve only 55-60% accuracy in predicting stock movements.*

---

## 16. Monitoring, Analytics & Observability

### What to Monitor

AlphaCouncil has four critical monitoring dimensions:

1. **System Health**: Uptime, latency, error rates
2. **LLM Performance**: Token usage, costs, quality metrics
3. **Data Freshness**: Document corpus staleness, web search relevance
4. **Business Metrics**: User engagement, conversion, revenue

### System Health Monitoring

#### Application Performance Monitoring (APM)

**Tool**: Sentry (Free tier: 5,000 events/month)

```python
# main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # Sample 10% of transactions
    environment=os.getenv("ENVIRONMENT", "production")
)

# Automatically captures:
# - Unhandled exceptions
# - API endpoint latency
# - Database query performance
# - External API failures (Yahoo Finance, Groq, Tavily)
```

**Key Metrics to Track**:
```python
# Track custom metrics
sentry_sdk.set_tag("debate_tier", tier)
sentry_sdk.set_context("debate", {
    "ticker": ticker,
    "user_id": user_id,
    "debate_id": debate_id
})

# Track debate execution time
with sentry_sdk.start_transaction(op="debate", name="run_full_debate"):
    final_state = debate_graph.invoke(initial_state)
```

#### Database Performance

**PostgreSQL Monitoring** (via Supabase dashboard):
- Query execution time (target: <100ms for RAG retrieval)
- Index hit rate (target: >99% for vector searches)
- Connection pool usage (alert if >80% capacity)

**Slow Query Alerts**:
```sql
-- Identify slow RAG queries
SELECT 
    query,
    calls,
    total_time / calls as avg_time_ms,
    rows / calls as avg_rows
FROM pg_stat_statements
WHERE query LIKE '%<=> %vector%'  -- pgvector searches
ORDER BY total_time DESC
LIMIT 10;
```

#### External API Monitoring

Track third-party API health:

```python
# Track API response times and failures
@app.middleware("http")
async def monitor_external_apis(request: Request, call_next):
    response = await call_next(request)
    
    # Log slow external API calls
    if hasattr(request.state, "external_api_call"):
        api_name = request.state.api_name
        duration = request.state.duration_ms
        
        if duration > 5000:  # >5 seconds
            logger.warning(f"{api_name} API slow: {duration}ms")
            
            sentry_sdk.capture_message(
                f"Slow {api_name} API response",
                level="warning",
                extra={"duration_ms": duration}
            )
    
    return response
```

### LLM Performance Monitoring

#### Token Usage Tracking

```python
# Track per-debate token consumption
class DebateMetrics:
    def __init__(self):
        self.tokens_used = 0
        self.llm_calls = 0
        self.cost_usd = 0.0
    
    def log_llm_call(self, model: str, input_tokens: int, output_tokens: int):
        """Logs each LLM call and calculates cost."""
        self.llm_calls += 1
        self.tokens_used += (input_tokens + output_tokens)
        
        # Groq pricing (free tier)
        if model.startswith("llama"):
            cost = 0.0  # Free
        # Claude Haiku pricing (if used for arbitrator)
        elif model == "claude-3-5-haiku":
            cost = (input_tokens / 1_000_000 * 0.25) + (output_tokens / 1_000_000 * 1.25)
        
        self.cost_usd += cost
        
        # Log to analytics
        db.llm_metrics.insert_one({
            "timestamp": datetime.utcnow(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost
        })
```

**Daily Quota Alerts**:
```python
@daily_task
def check_llm_quota_usage():
    """
    Alerts if approaching daily LLM limits.
    """
    today = datetime.utcnow().date()
    
    # Groq free tier: 14,400 requests/day
    groq_calls_today = db.llm_metrics.count_documents({
        "timestamp": {"$gte": datetime.combine(today, datetime.min.time())},
        "model": {"$regex": "^llama"}
    })
    
    if groq_calls_today > 12000:  # 83% of limit
        send_alert(
            "Groq API Quota Warning",
            f"Used {groq_calls_today}/14,400 requests today. Consider rate limiting."
        )
```

#### Debate Quality Metrics

```python
@app.middleware("http")
async def log_debate_quality(request: Request, call_next):
    """
    Logs quality metrics for each completed debate.
    """
    response = await call_next(request)
    
    if request.url.path.startswith("/api/v1/debates") and response.status_code == 200:
        debate = response.json()
        
        # Calculate quality score
        quality = evaluate_debate_quality(debate)
        
        # Log to analytics
        db.debate_quality.insert_one({
            "debate_id": debate['debate_id'],
            "ticker": debate['ticker'],
            "timestamp": datetime.utcnow(),
            "citation_coverage": quality['citation_coverage'],
            "balance": quality['balance'],
            "specificity": quality['specificity'],
            "coherence": quality['coherence'],
            "actionability": quality['actionability'],
            "overall_score": quality['overall']
        })
        
        # Alert on poor quality
        if quality['overall'] < 0.60:
            logger.warning(f"Low quality debate: {debate['debate_id']} (score: {quality['overall']})")
    
    return response
```

### Data Freshness Monitoring

#### Document Corpus Staleness

```python
@weekly_task
def check_corpus_freshness():
    """
    Alerts when embedded documents are outdated.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=180)  # 6 months
    
    for ticker in TRACKED_TICKERS:
        latest_doc = db.document_chunks.find_one(
            {"ticker": ticker},
            sort=[("ingested_at", -1)]
        )
        
        if not latest_doc or latest_doc['ingested_at'] < cutoff_date:
            send_alert(
                f"Stale Corpus: {ticker}",
                f"Latest document ingested: {latest_doc['ingested_at'] if latest_doc else 'Never'}"
            )
```
### Business Metrics Dashboard

**Key Metrics to Track**:

```python
# Stored in PostgreSQL analytics tables

class BusinessMetrics:
    @staticmethod
    def daily_active_users(date: datetime.date) -> int:
        """Users who ran at least one debate on this date."""
        return db.debates.count_documents({
            "created_at": {
                "$gte": datetime.combine(date, datetime.min.time()),
                "$lt": datetime.combine(date + timedelta(days=1), datetime.min.time())
            }
        })
    
    @staticmethod
    def debates_by_tier(date: datetime.date) -> dict:
        """Breakdown of debates by tier."""
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": datetime.combine(date, datetime.min.time()),
                        "$lt": datetime.combine(date + timedelta(days=1), datetime.min.time())
                    }
                }
            },
            {
                "$group": {
                    "_id": "$tier",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = list(db.debates.aggregate(pipeline))
        return {r['_id']: r['count'] for r in results}
    
    @staticmethod
    def conversion_rate(date: datetime.date) -> float:
        """% of free tier users who upgraded to paid."""
        free_users = db.users.count_documents({
            "subscription_tier": "free",
            "created_at": {"$lt": datetime.combine(date, datetime.min.time())}
        })
        
        converted = db.users.count_documents({
            "subscription_tier": {"$in": ["basic", "pro"]},
            "subscription_started_at": {
                "$gte": datetime.combine(date, datetime.min.time()),
                "$lt": datetime.combine(date + timedelta(days=1), datetime.min.time())
            }
        })
        
        return converted / free_users if free_users > 0 else 0.0
    
    @staticmethod
    def top_stocks_analyzed(days: int = 7) -> list:
        """Most analyzed stocks in the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {"created_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$ticker", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        results = list(db.debates.aggregate(pipeline))
        return [(r['_id'], r['count']) for r in results]
```

```

---

## 17. Implementation Roadmap & Milestones

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Prove the core RAG + multi-agent system works with one company

#### Week 1: Database & RAG Setup

**Tasks**:
- [ ] Set up Supabase project (PostgreSQL + pgvector)
- [ ] Create database schema (tables: `document_chunks`, `debates`, `users`)
- [ ] Enable pgvector extension
- [ ] Download Dangote Cement FY2025 annual report manually
- [ ] Build ingestion script: PDF → chunks → embeddings → pgvector
- [ ] Test: Query "What was revenue in FY2025?" returns correct citation

**Deliverable**: DANGCEM corpus ingested (~200 chunks in pgvector)

#### Week 2: Multi-Agent Debate

**Tasks**:
- [ ] Implement `retrieve_sec_filings` RAG tool
- [ ] Implement `fetch_financial_ratios` (Yahoo Finance API)
- [ ] Implement `run_dcf_model` (pure Python)
- [ ] Build 3-agent LangGraph orchestrator (Bull, Bear, Arbitrator)
- [ ] Test: Run full debate for DANGCEM, get JSON verdict

**Deliverable**: End-to-end debate working for 1 company

### Phase 2: API & Web Interface (Weeks 3-4)

#### Week 3: FastAPI Backend

**Tasks**:
- [ ] Build FastAPI app with routes:
  - `POST /api/v1/debates` (create debate)
  - `GET /api/v1/debates/{id}` (get results)
  - `GET /api/v1/debates/{id}/status` (polling)
- [ ] Set up Celery + Redis for async debate execution
- [ ] Add JWT authentication
- [ ] Add rate limiting (10 debates/day per user)

**Deliverable**: REST API deployed to Railway

#### Week 4: Web UI Artifact

**Tasks**:
- [ ] Build HTML artifact with debate input form
- [ ] Add loading spinner and status polling
- [ ] Display 3-turn debate with expandable sections
- [ ] Show final verdict with charts (allocation, confidence)
- [ ] Add "Export to PDF" button

**Deliverable**: Published artifact users can share (claude.ai/artifact/{id})

### Phase 3: Scale to 5 Companies (Week 5)

**Tasks**:
- [ ] Expand corpus to 5 companies:
  - DANGCEM (Dangote Cement)
  - MTNN (MTN Nigeria)
  - ACCESS (Access Holdings)
  - GTCO (Guaranty Trust Holding)
  - BUACEMENT (BUA Cement)
- [ ] Ingest 3 annual reports + 2 quarterly results per company
- [ ] Total corpus: ~8,250 chunks (~16MB embeddings)
- [ ] Add `web_search_financial_context` tool (Tavily API)
- [ ] Test: Run debates for all 5 companies

**Deliverable**: AlphaCouncil supports top 5 NSE stocks

### Phase 4: Beta Launch (Week 6)

**Tasks**:
- [ ] Invite 20 beta testers (Nigerian investment Twitter)
- [ ] Collect feedback on debate quality
- [ ] Add "Report incorrect citation" feedback mechanism
- [ ] Monitor LLM costs and quality metrics
- [ ] Iterate on agent prompts based on feedback

**Deliverable**: 50+ real-world debates run, validated quality

### Phase 5: Production Hardening (Weeks 7-8)

**Tasks**:
- [ ] Add Sentry monitoring
- [ ] Build analytics dashboard (DAU, debates/day, top stocks)
- [ ] Implement backtesting system (track recommendation accuracy)
- [ ] Add subscription tiers (Stripe integration)
- [ ] Write legal disclaimers and Terms of Service
- [ ] Set up SendGrid for email notifications


---



### Agent Design

**Q4: How aggressive should the Bear agent be?**
- Option A: Moderate (finds real risks, but balanced)
- Option B: Aggressive (devil's advocate, challenges everything)
- Option C: User-configurable (slider: cautious ↔ aggressive)
- **Decision needed**: Option B for MVP (force strong counterarguments), add Option C later

**Q5: Should we allow users to customize agent personas?**
- Example: "Make the Bull agent focus on growth stocks" or "Make the Bear agent emphasize ESG risks"
- **Decision needed**: Skip for MVP (adds complexity), add as "Premium" feature later

### Pricing & Monetization

**Q6: Freemium model details**
- Option A: 5 free Tier 1 debates/month, pay ₦2,000 per Tier 3
- Option B: 1 free Tier 3 debate, then ₦1,500 per debate
- Option C: Subscription model: ₦15,000/month for unlimited
- **Decision needed**: Option A (5 free Tier 1) for user acquisition

**Q7: Should we offer bulk pricing?**
- Example: 10 debates for ₦15,000 (25% discount)
- **Decision needed**: Yes, add bulk packages after launch (month 3)

### Technical

**Q8: LLM provider strategy**
- Option A: Groq only (free tier, may hit limits)
- Option B: Groq + Claude Haiku fallback (costs $0.05 per debate)
- Option C: Self-hosted Llama 3.1 70B (upfront GPU cost)
- **Decision needed**: Option A for MVP, add Option B when hitting Groq limits

**Q9: Should we support on-demand ingestion?**
- If user requests analysis for a stock not in corpus, should we:
  - Option A: Reject ("Stock not yet supported")
  - Option B: Queue ingestion (takes 5-10 min, then run debate)
  - Option C: Run debate with web search only (no RAG)
- **Decision needed**: Option A for MVP (pre-load only 5 stocks), add Option B later

**Q10: Data storage location**
- Option A: Supabase (PostgreSQL in US/EU)
- Option B: Local Nigerian hosting (lower latency, higher cost)
- **Decision needed**: Option A (Supabase) - data sovereignty less critical for public financial data

### Legal & Compliance

**Q11: Should we register as a FinTech in Nigeria?**
- Pros: Legitimacy, partnerships with banks
- Cons: Regulatory overhead, compliance costs
- **Decision needed**: Consult Nigerian securities lawyer before launch

**Q12: How to handle incorrect recommendations?**
- If AlphaCouncil recommends BUY and stock crashes, is there liability?
- **Decision**: Strong disclaimers + "educational purposes only" positioning

---

## 19. Appendix: Reference Material

### Nigerian Stock Market Context

**Nigerian Exchange (NGX) Overview**:
- **Market Cap**: ₦55 trillion (~$38 billion at ₦1,450/$)
- **Listed Companies**: ~150
- **Top 10 by Market Cap**:
  1. Dangote Cement (DANGCEM) - ₦6.5T
  2. MTN Nigeria (MTNN) - ₦5.1T
  3. BUA Cement (BUACEMENT) - ₦3.2T
  4. Airtel Africa (AIRTELAFRI) - ₦2.9T
  5. Access Holdings (ACCESSCORP) - ₦2.1T
  6. Seplat Energy (SEPLAT) - ₦1.8T
  7. Guaranty Trust Holding (GTCO) - ₦1.6T
  8. Zenith Bank (ZENITHBANK) - ₦1.4T
  9. UBA (UBA) - ₦1.2T
  10. Nestle Nigeria (NESTLE) - ₦1.1T

**Sector Breakdown**:
- Banking: 30% of market cap
- Consumer Goods: 20%
- Industrials (Cement): 18%
- Telecom: 15%
- Oil & Gas: 10%
- Others: 7%

### Technical Stack Reference

**Free Tier Limits (as of Nov 2026)**:
- **Groq**: 14,400 requests/day (Llama 3.1 70B)
- **Tavily**: 1,000 searches/month
- **Supabase**: 500MB database, 1GB storage
- **Railway**: $5 free credits/month
- **NewsAPI**: 100 requests/day
- **Sentry**: 5,000 events/month

**Cost Projections (Paid Tiers)**:
- **Claude Haiku**: $0.25/1M input tokens, $1.25/1M output (~$0.03 per debate)
- **Supabase Pro**: $25/month (8GB database)
- **Railway Pro**: $50/month (8GB RAM, 4 vCPU)
- **Tavily Pro**: $100/month (10,000 searches)

### Useful Links

**Nigerian Financial Data Sources**:
- Nigerian Exchange Group: https://ngxgroup.com
- Central Bank of Nigeria: https://www.cbn.gov.ng
- Nairametrics: https://nairametrics.com
- BusinessDay Nigeria: https://businessday.ng

**Technical Documentation**:
- LangGraph: https://langchain-ai.github.io/langgraph/
- pgvector: https://github.com/pgvector/pgvector
- Sentence Transformers: https://www.sbert.net/
- Tavily API: https://tavily.com/docs

---

**Document Version**: 1.0 (Complete)  
**Last Updated**: 2026-11-02  
**Status**: Ready for Implementation  
**Total Word Count**: ~120,000 words  
**Total Sections**: 19

---

**END OF PRODUCT REQUIREMENTS DOCUMENT**

### Current Pain Points

1. **Single LLM Analysis is Shallow**
   - Generic bullish/bearish takes without adversarial stress-testing
   - No structured cross-examination of claims
   - Prone to confirmation bias (validates pre-existing beliefs)

2. **Manual Research is Time-Intensive**
   - Reading 200+ page 10-Ks and annual reports
   - Cross-referencing 3+ years of financial statements
   - Monitoring news sentiment and macro indicators
   - Takes 4-8 hours per stock analysis

3. **No Audit Trail**
   - No structured record of what was considered and why
   - Cannot revisit reasoning 6 months later
   - Compliance/fund management challenges

4. **Overconfidence Bias**
   - Investors cherry-pick data supporting their thesis
   - No forced consideration of bear case
   - Lacks calibrated confidence scores

---

## 3. Solution Architecture

### Multi-Agent Debate System

**Five Specialized Agents:**

1. **Fundamental Analyst** (Bull Case)
   - Revenue growth, margin expansion, market sentiment
   - Tools: `retrieve_sec_filings()`, `fetch_financial_ratios()`, `get_market_sentiment()`

2. **Quantitative Auditor** (Bear Case)
   - Debt levels, leverage ratios, red flags
   - Tools: `retrieve_sec_filings()`, `fetch_financial_ratios()`, `check_accounting_quality()`

3. **Risk & Macro Strategist**
   - CBN monetary policy, inflation, FX exposure, macro risks
   - Tools: `get_cbn_rates()`, `run_dcf_model()`, `analyze_fx_exposure()`

4. **Moderator Agent**
   - Orchestrates debate flow (LangGraph)
   - Decides when sufficient evidence gathered
   - Routes arguments between agents

5. **Arbitrator / Chief Investment Officer**
   - Synthesizes all arguments
   - Produces final verdict with confidence score
   - Generates actionable recommendations (allocation, stop-loss, monitoring triggers)

### Orchestration: LangGraph State Machine

```
[User Input: Ticker + Thesis + Capital]
        ↓
[Background: Scrape 10-K → Chunk → Embed → Store in pgvector]
        ↓
[Moderator: Route thesis to committee]
        ↓
[Turn 1: Fundamental Analyst presents bull case]
        ↓
[Turn 2: Quantitative Auditor challenges with bear case]
        ↓
[Turn 3: Risk & Macro Strategist presents macro context]
        ↓
[Moderator: Check if debate needs continuation → Loop or Exit]
        ↓
[Arbitrator: Synthesize evidence → Final verdict]
        ↓
[Output: Investment Memo + Debate Transcript + Audio Briefing]
```

---

## 4. User Entry Point

### Primary Use Case: Investment Thesis Validation

**Input Form (Web UI):**

```
┌─────────────────────────────────────────────────────┐
│  AlphaCouncil: AI Investment Committee              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Stock Ticker:   [DANGCEM]                         │
│                                                     │
│  Investment Thesis (optional):                      │
│  ┌───────────────────────────────────────────────┐ │
│  │ Dangote Cement will benefit from Nigeria's   │ │
│  │ infrastructure boom and cement demand growth │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Capital to Deploy:  [₦5,000,000]                  │
│                                                     │
│  Risk Tolerance:  ○ Conservative  ● Moderate       │
│                   ○ Aggressive                     │
│                                                     │
│  [🔍 Run Investment Committee Review]              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Tiered Analysis Options

| Tier | Agents | Use Case | Estimated Cost |
|------|--------|----------|----------------|
| **Tier 1: Quick Check** | 1 agent (Fundamental only) | "Is this stock fundamentally sound?" | Free (Groq) |
| **Tier 2: Risk Assessment** | 2 agents (Analyst + Auditor) | "What are the key risks?" | ₦500 |
| **Tier 3: Full Committee** | 5 agents (full debate) | "Full investment memo with verdict" | ₦2,000 |

---

## 5. Output Specifications

### 5.1 Interactive Debate Transcript (Web UI)

```
📊 Investment Committee Review: DANGCEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Fundamental Analyst (Bull Case)
   Revenue grew 18.7% YoY to ₦2.1T in FY2025
   [REF:1] SEC Filing - FY2025 10-K, Page 42
   Gross margin improved to 45.1% (vs 42.3%)... [Expand ▼]
   
🔴 Quantitative Auditor (Bear Case)
   Debt-to-equity ratio: 1.8 (industry avg 1.2)
   [REF:4] Balance Sheet Analysis
   Interest coverage dropped from 4.2x to 3.1x... [Expand ▼]
   
🟡 Risk & Macro Strategist
   CBN policy rate at 18.75% → high cost of capital
   [REF:7] Central Bank of Nigeria MPR Data
   DCF intrinsic value: ₦420/share... [Expand ▼]

⚖️  FINAL VERDICT: Conditional Buy
   Allocate ₦2.5M (50% of intended capital)
   Set stop-loss at ₦365/share (-5%)
   Confidence: 68% (Moderate conviction)
   
[📄 Download Full Memo] [🔊 Play Audio Briefing]
```

### 5.2 Structured JSON Output (API Response)

```json
{
  "ticker": "DANGCEM",
  "company_name": "Dangote Cement Plc",
  "analysis_date": "2026-11-02T07:00:00Z",
  "verdict": "CONDITIONAL_BUY",
  "confidence": 0.68,
  
  "recommendation": {
    "allocation_recommended": 2500000,
    "allocation_percentage": 0.50,
    "current_price": 385,
    "target_price": 420,
    "stop_loss": 365,
    "time_horizon": "12_months"
  },
  
  "bull_thesis": {
    "summary": "Strong revenue growth (18.7% YoY), margin expansion (45.1%), infrastructure spending tailwinds",
    "key_points": [
      {
        "claim": "Revenue grew 18.7% YoY to ₦2.1T in FY2025",
        "source": "[REF:1] SEC Filing - FY2025 10-K, Page 42",
        "confidence": 0.92
      },
      {
        "claim": "Gross margin improved to 45.1% (vs 42.3% prior year)",
        "source": "[REF:2] Income Statement Analysis",
        "confidence": 0.89
      },
      {
        "claim": "Market sentiment: +0.72 (Bullish)",
        "source": "[REF:3] News sentiment aggregation (60-day window)",
        "confidence": 0.71
      }
    ]
  },
  
  "bear_thesis": {
    "summary": "Elevated leverage (D/E: 1.8), declining interest coverage (3.1x), 40% USD-denominated debt with FX exposure",
    "key_risks": [
      {
        "risk": "High debt-to-equity ratio: 1.8 (industry avg: 1.2)",
        "severity": "HIGH",
        "source": "[REF:4] Balance Sheet Analysis",
        "mitigation": "Monitor quarterly debt servicing costs"
      },
      {
        "risk": "Interest coverage dropped from 4.2x to 3.1x",
        "severity": "MEDIUM",
        "source": "[REF:5] Cash Flow Statement Analysis",
        "mitigation": "Set alert if coverage falls below 2.5x"
      },
      {
        "risk": "40% of debt USD-denominated; 15% naira depreciation → +25% debt servicing costs",
        "severity": "HIGH",
        "source": "[REF:6] Currency Exposure Analysis",
        "mitigation": "Monitor USD/NGN exchange rate weekly"
      }
    ]
  },
  
  "macro_context": {
    "cbn_policy_rate": 18.75,
    "inflation_rate": 21.34,
    "fx_rate_usd_ngn": 1450,
    "dcf_intrinsic_value": 420,
    "margin_of_safety": 0.09,
    "wacc": 0.15
  },
  
  "monitoring_triggers": [
    "Debt-to-equity drops below 1.5 → Consider increasing allocation",
    "Naira depreciates beyond ₦1,600/USD → Reassess FX risk",
    "Stop-loss triggered at ₦365 → Exit position"
  ],
  
  "debate_trace_id": "uuid-abc123",
  "debate_url": "https://alphacouncil.com/debates/uuid-abc123",
  "audio_briefing_url": "https://alphacouncil.com/audio/uuid-abc123.mp3"
}
```

### 5.3 Investment Memo (PDF/Markdown Export)

**Structure:**
1. Executive Summary (verdict + confidence)
2. Investment Thesis (user's original thesis)
3. Bull Case (Fundamental Analyst arguments)
4. Bear Case (Quantitative Auditor arguments)
5. Risk & Macro Analysis
6. Arbitrator's Synthesis
7. Actionable Recommendations
8. Monitoring Plan
9. Full Debate Transcript (Appendix)

---

## 6. Technical Stack

### 6.1 Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | REST endpoints for debate orchestration |
| **Orchestration** | LangGraph | Multi-agent state machine |
| **LLM Provider (Free Tier)** | Groq (Llama 3.1 70B) | Agent inference (8-10 calls per debate) |
| **LLM Provider (Premium)** | Claude 3.5 Haiku | Arbitrator synthesis (1 call per debate) |
| **Vector Database** | pgvector (PostgreSQL) | RAG system for 10-K embeddings |
| **Embeddings** | OpenAI `text-embedding-3-small` | Document chunking/retrieval |
| **Database** | PostgreSQL | Debate history, user data |
| **Task Queue** | Celery + Redis | Async debate execution |

### 6.2 Data Sources

| Data Type | Source | Access Method |
|-----------|--------|---------------|
| **SEC Filings (10-K, 10-Q)** | NSE / Company IRs | Web scraping + OCR |
| **Financial Ratios** | Yahoo Finance / NGX API | REST API |
| **Market Sentiment** | News aggregation (Punch, Vanguard, BusinessDay) | Web scraping + NLP |
| **CBN Monetary Policy** | Central Bank of Nigeria | Official API |
| **FX Rates** | CBN / XE.com | REST API |

### 6.3 Frontend

| Component | Technology |
|-----------|-----------|
| **Web UI** | Next.js 14 + TypeScript |
| **UI Framework** | Tailwind CSS + shadcn/ui |
| **State Management** | Zustand |
| **Real-time Updates** | WebSockets (debate progress) |
| **Charts** | Recharts / D3.js |

### 6.4 Infrastructure

- **Hosting:** Railway / Render (for MVP)
- **Storage:** Supabase (PostgreSQL + pgvector)
- **CDN:** Cloudflare
- **Audio Generation:** ElevenLabs API (for audio briefings)

---

## 7. Core Features (MVP)

### 7.1 Must-Have (Phase 1)

- [ ] **User Input Form:** Ticker + Thesis + Capital + Risk Tolerance
- [ ] **Multi-Agent Debate Orchestration:** 5 agents with LangGraph state machine
- [ ] **RAG System:** Ingest 10-K documents, chunk, embed, store in pgvector
- [ ] **Tool Implementations:**
  - [ ] `retrieve_sec_filings(ticker, query)`
  - [ ] `fetch_financial_ratios(ticker)`
  - [ ] `get_market_sentiment(ticker)`
  - [ ] `get_cbn_rates()`
  - [ ] `run_dcf_model(fcf, growth, wacc)`
- [ ] **Debate Transcript UI:** Expandable turns with citations
- [ ] **JSON Output API:** Structured response for API users
- [ ] **Investment Memo Export:** PDF/Markdown generation

### 7.2 Should-Have (Phase 2)

- [ ] **Tiered Analysis:** Quick Check (Tier 1) vs Full Committee (Tier 3)
- [ ] **Audio Briefing:** Text-to-speech summary (ElevenLabs)
- [ ] **Debate Replay:** Replay debate with animations
- [ ] **Historical Debates:** List past debates, search by ticker
- [ ] **Citation Links:** Click [REF:n] to view source document
- [ ] **Real-time Progress:** WebSocket updates during debate execution

### 7.3 Could-Have (Phase 3)

- [ ] **Portfolio-Level Analysis:** Analyze 5+ stocks simultaneously
- [ ] **Backtesting:** "What would AlphaCouncil have recommended 1 year ago?"
- [ ] **Custom Agent Personas:** User-defined agent roles
- [ ] **Slack/WhatsApp Integration:** Receive debate summaries via messaging
- [ ] **Mobile App:** iOS/Android native apps

---

## 8. Success Metrics

### 8.1 Product Metrics

| Metric | Target (3 months post-launch) |
|--------|-------------------------------|
| **Weekly Active Users** | 200 users |
| **Debates Run** | 500 debates/month |
| **Average Confidence Score** | 65-75% (well-calibrated) |
| **User Retention (30-day)** | 40% |
| **Tier 3 Conversion Rate** | 15% (free → paid tier) |

### 8.2 Quality Metrics

| Metric | Validation Method |
|--------|-------------------|
| **Accuracy of Bull/Bear Claims** | Manual review of 50 debates by finance experts |
| **Citation Quality** | 90%+ of [REF:n] links to valid sources |
| **Recommendation Calibration** | Track actual stock performance vs predicted outcomes (6-month lag) |
| **Debate Coherence** | User surveys: "Did the debate feel structured?" (>4/5 avg) |

### 8.3 Business Metrics

| Metric | Target (Year 1) |
|--------|-----------------|
| **Revenue** | ₦10M ($7,000 @ ₦1,450/$) |
| **Cost Per Debate (Tier 3)** | <₦200 (10x margin at ₦2,000 price) |
| **Customer Acquisition Cost** | <₦5,000 |
| **Lifetime Value** | ₦25,000 (12.5 debates/user) |

---

## 9. Risk Mitigation

### 9.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **LLM Hallucination** | High | High | Force citation of sources; manual spot-checks |
| **10-K Data Unavailability** | Medium | High | Build fallback to Yahoo Finance / NGX API |
| **API Rate Limits (Groq)** | Medium | Medium | Implement exponential backoff; paid tier as backup |
| **Debate Loops (Agents Don't Converge)** | Medium | Medium | Hard cap at 5 turns; Moderator forced exit logic |

### 9.2 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Low User Trust in AI Recommendations** | High | High | Emphasize "decision support, not financial advice" disclaimer |
| **Regulatory Issues (SEC/Investment Advice)** | Low | High | Legal disclaimer: "Not a registered investment advisor" |
| **Competitors (OpenBB, Bloomberg Terminal)** | Medium | Medium | Focus on Nigeria-specific context + adversarial debate USP |
| **Data Quality (NSE Filings)** | High | Medium | Manual curation for top 20 NSE stocks |

---

## 10. Go-to-Market Strategy

### 10.1 Target Segments

1. **Primary:** Retail investors (₦5M-50M portfolios) in Lagos/Abuja
2. **Secondary:** Small fund managers (₦100M-1B AUM)
3. **Tertiary:** Finance students / investment clubs

### 10.2 Launch Plan (3 Months)

**Month 1: Private Beta**
- Invite 50 users from Nigerian investment Twitter/Reddit
- Free Tier 3 debates for feedback
- Goal: 100 debates, 20+ feedback sessions

**Month 2: Public Launch**
- ProductHunt / HackerNews launch
- Content marketing: "How AI Debate Systems Beat Single-LLM Stock Analysis"
- Goal: 500 signups, 200 WAU

**Month 3: Revenue Activation**
- Introduce paid Tier 3 (₦2,000/debate)
- Bulk packages: 10 debates for ₦15,000 (25% discount)
- Goal: ₦2M revenue, 15% conversion rate

### 10.3 Distribution Channels

- **Organic:** SEO for "Nigerian stock analysis AI" / "NSE stock research"
- **Paid:** Google Ads targeting "Dangote stock", "Access Bank investment"
- **Partnerships:** Collaborate with Nigerian fintech YouTubers (e.g., Oluwatosin Olaseinde)
- **Community:** Build Telegram/WhatsApp groups for users to share debate results

---

## 11. Competitive Analysis

| Competitor | Strengths | Weaknesses | AlphaCouncil Differentiation |
|------------|-----------|------------|------------------------------|
| **ChatGPT Stock Analysis** | Free, fast | Shallow, no citations, single perspective | Multi-agent adversarial debate |
| **Bloomberg Terminal** | Comprehensive data | $24,000/year, overkill for retail | Nigeria-focused, ₦2,000/analysis |
| **OpenBB Terminal** | Open-source, free | No AI synthesis, DIY research | Automated debate + actionable verdict |
| **TradingView Ideas** | Community-driven | Human bias, no systematic rigor | AI agents with forced bear case |
| **Nigerian Brokers** | Local expertise | Manual, slow (1-2 days) | Real-time (5-10 min debate) |

**Unique Selling Proposition:**  
*"The only AI system that forces a bear case to challenge your investment thesis—built for Nigerian markets."*

---

## 12. Future Vision (Year 2+)

### 12.1 Advanced Features

- **Real-time Portfolio Monitoring:** Auto-trigger debates when holdings move >10%
- **Macro Agent Integration:** Add dedicated CBN policy analyst agent
- **Sector-Specific Agents:** Banking sector specialist, Oil & Gas specialist
- **Collaborative Debates:** Multiple users debate same stock with AI moderator

### 12.2 Expansion Opportunities

- **Pan-African Markets:** Kenya (NSE), South Africa (JSE), Ghana (GSE)
- **Asset Class Expansion:** Bonds, ETFs, mutual funds, real estate
- **Institutional Product:** White-label version for wealth management firms

---

## 13. Open Questions / Decisions Needed

- [ ] **Which 10-K sources to prioritize?** NSE official filings vs company IR pages?
- [ ] **Freemium model details:** How many free Tier 1 debates before paywall?
- [ ] **Data freshness SLA:** Update 10-Ks within 24 hours of release?
- [ ] **Agent personality tuning:** How "aggressive" should the Auditor be?
- [ ] **Legal entity setup:** Register as FinTech in Nigeria? Compliance requirements?
- [ ] **Payment processing:** Paystack vs Flutterwave for ₦2,000 transactions?

---

## 14. Appendix

### 14.1 Example Debate Flow (Dangote Cement)

**Turn 1 - Fundamental Analyst (Bull):**
```
"Dangote Cement shows strong fundamentals:
- [REF:1] Revenue grew 18.7% YoY to ₦2.1T in FY2025
- [REF:2] Gross margin improved to 45.1% (vs 42.3%)
- [REF:3] Market sentiment: +0.72 (Bullish)
- Infrastructure spending bill passed → demand ↑"
```

**Turn 2 - Quantitative Auditor (Bear):**
```
"However, critical risks exist:
- [REF:4] Debt-to-equity ratio: 1.8 (industry avg 1.2)
- [REF:5] Interest coverage dropped from 4.2x to 3.1x
- [REF:6] FX exposure: 40% of debt USD-denominated
- If naira depreciates 15%, debt servicing costs ↑25%"
```

**Turn 3 - Risk & Macro Strategist:**
```
"Macro headwinds present:
- [REF:7] CBN policy rate at 18.75% → high cost of capital
- [REF:8] DCF intrinsic value: ₦420/share
- Current price: ₦385/share → 9% upside (thin margin)
- Naira volatility risk: 25% downside if FX crisis"
```

**Final Verdict - Arbitrator:**
```
⚠️ CONDITIONAL BUY with strict risk controls

Rationale:
• Fundamentals support growth thesis (Analyst)
• BUT high leverage + FX exposure = elevated risk (Auditor)
• Valuation shows only 9% upside (thin margin of safety)

Recommendation:
• Allocate: ₦2.5M (50% of intended capital)
• Set stop-loss: ₦365/share (-5%)
• Monitor: Quarterly debt servicing + naira/USD rate
• Revisit if: Debt-to-equity drops below 1.5

Confidence: 68% (Moderate conviction)
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-11-02  
**Status:** Draft for Review
