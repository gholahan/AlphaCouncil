"""CBN Scraper - Call the actual API endpoint that the page uses."""

import asyncio
import httpx
from datetime import datetime


async def get_cbn_rates() -> dict:
    """
    Fetch CBN exchange rates by calling the API endpoint the website uses.

    Returns:
        {
            "monetary_policy_rate": None,  # Not available from this endpoint
            "inflation_rate": None,         # Not available from this endpoint
            "usd_exchange_rate": 1625.0,   # Latest NFEM closing rate
            "last_updated": "2024-11-01"
        }
    """

    api_url = "https://www.cbn.gov.ng/api/GetAllNFEM_RatesGRAPH"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(api_url)

            if response.status_code != 200:
                return {
                    "error": f"API returned status {response.status_code}",
                    "monetary_policy_rate": None,
                    "inflation_rate": None,
                    "usd_exchange_rate": None,
                    "last_updated": None
                }

            data = response.json()

            if not data or len(data) == 0:
                return {
                    "error": "No data returned from API",
                    "monetary_policy_rate": None,
                    "inflation_rate": None,
                    "usd_exchange_rate": None,
                    "last_updated": None
                }

            # Get the most recent rate (first item)
            latest = data[0]

            closing_rate = float(latest.get("closingrate", 0))
            rate_date = latest.get("ratedate", "")

            return {
                "monetary_policy_rate": None,
                "inflation_rate": None,
                "usd_exchange_rate": closing_rate,
                "last_updated": rate_date
            }

    except Exception as e:
        return {
            "error": str(e),
            "monetary_policy_rate": None,
            "inflation_rate": None,
            "usd_exchange_rate": None,
            "last_updated": None
        }


async def main():
    print("Fetching CBN rates from API endpoint...\n")
    result = await get_cbn_rates()

    print("Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    print(f"\nType: {type(result)}")


if __name__ == "__main__":
    asyncio.run(main())
