"""
MCP Monitoring Tools - Measurable indicators and reassessment triggers for the CIO report.
"""

from langchain_core.tools import tool

@tool
async def generate_monitoring_indicators(
    ticker: str,
    sector: str = "General",
) -> dict:
    """
    Generate thesis-specific measurable indicators and reassessment triggers
    for Section 7 (What to monitor) of the CIO Investment Decision Report.
    """
    return {
        "ticker": ticker.upper(),
        "indicators": [
            {
                "indicator_name": "Revenue Growth Rate (YoY)",
                "why_it_matters": "Core driver of business expansion and market share capture",
                "positive_development": "YoY growth exceeding 15%",
                "concerning_development": "YoY growth dropping below 5%",
                "reassessment_trigger": "Two consecutive quarters of revenue contraction",
            },
            {
                "indicator_name": "Operating Margin",
                "why_it_matters": "Reflects pricing power and cost discipline amid inflation",
                "positive_development": "Margin expansion or stability",
                "concerning_development": "Significant margin compression from rising COGS",
                "reassessment_trigger": "Operating margin decline exceeding 300 bps YoY",
            },
            {
                "indicator_name": "Free Cash Flow & Leverage",
                "why_it_matters": "Ensures dividend sustainability and solvency",
                "positive_development": "Positive FCF generation and debt reduction",
                "concerning_development": "Negative FCF and rising net debt-to-EBITDA above 3.0x",
                "reassessment_trigger": "Inability to service debt obligations or dividend suspension",
            },
        ]
    }
