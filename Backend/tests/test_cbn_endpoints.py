"""Test multiple CBN endpoints to find actual rate data."""

import asyncio
import httpx
from bs4 import BeautifulSoup


async def test_cbn_endpoints():
    """Test different CBN pages to find where rate data actually lives."""

    endpoints = [
        ("Exchange Rates by Currency", "https://www.cbn.gov.ng/rates/ExchRateByCurrency.html"),
        ("Monthly Average Exchange Rates", "https://www.cbn.gov.ng/rates/exrate.html"),
        ("Interbank Rates", "https://www.cbn.gov.ng/rates/interbankrates.html"),
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
        for name, url in endpoints:
            print(f"\n{'='*70}")
            print(f"{name}")
            print(f"{url}")
            print('='*70)

            try:
                response = await client.get(url)

                if response.status_code != 200:
                    print(f"Failed: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                tables = soup.find_all('table')

                print(f"Found {len(tables)} table(s)")

                for i, table in enumerate(tables):
                    rows = table.find_all('tr')
                    data_rows = [r for r in rows if r.find_all('td')]

                    print(f"\nTable {i+1}: {len(rows)} total rows, {len(data_rows)} data rows")

                    if data_rows:
                        print("First 3 data rows:")
                        for j, row in enumerate(data_rows[:3]):
                            cols = row.find_all('td')
                            cols_text = [c.get_text(strip=True) for c in cols]
                            print(f"  {cols_text}")
                    else:
                        print("  (No data rows - might be JavaScript-loaded)")

            except Exception as e:
                print(f"Error: {e}")


async def main():
    await test_cbn_endpoints()

    print("\n" + "="*70)
    print("CONCLUSION:")
    print("If all pages show 0 data rows, the CBN data is likely loaded via")
    print("JavaScript/AJAX, not static HTML. We'll need to use an API or")
    print("fallback to a database-backed approach.")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
