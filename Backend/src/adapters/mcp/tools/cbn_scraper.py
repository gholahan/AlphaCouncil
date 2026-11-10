"""MCP CBN Scraper Tool - Return full JSON array from CBN NFEM rates API."""

from langchain_core.tools import tool
import httpx


@tool
async def get_cbn_fx_rates() -> list:
    """
    Scrapes Central Bank of Nigeria website for current macro data.
    Returns the full list of NFEM rates returned by the CBN API.

    Returns:
        List of dicts containing NFEM exchange rates over time.
    """
    api_url = "https://www.cbn.gov.ng/api/GetAllNFEM_RatesGRAPH"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"
    }

    try:
        asyncx_client = httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers)
        async with asyncx_client as client:
            response = await client.get(api_url)

            if response.status_code != 200:
                return [{"error": f"API returned status {response.status_code}"}]

            data = response.json()

            if not isinstance(data, list):
                return [{"error": "Invalid response format from CBN API"}]

            return data

    except Exception as e:
        return [{"error": str(e)}]
