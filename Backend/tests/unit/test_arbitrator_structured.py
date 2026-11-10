import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock
from src.adapters.orchestration.langgraph_engine import LangGraphDebateEngine
from src.adapters.orchestration.arbitrator_schemas import (
    ArbitratorResponse,
    calculate_recommendation as _calculate_recommendation,
)
from src.adapters.mcp.tools.dcf_calculator import run_dcf_model


def test_arbitrator_response_validation():
    """Test Pydantic validation for ArbitratorResponse schema including chat_response."""
    data = {
        "verdict": "BUY",
        "investment_thesis": "Strong growth prospects and dominant market position supporting expansion.",
        "valuation_assessment": "Undervalued based on DCF model and peer multiples.",
        "time_horizon": "12 months",
        "rationale": "The bull case strongly outweighs the bear risks given solid fundamental momentum.",
        "bull_arguments_accepted": ["Revenue growth accelerating", "Market share expansion"],
        "bear_arguments_accepted": ["FX volatility"],
        "unresolved_risks": ["Regulatory changes"],
        "conditions_that_would_change_verdict": ["Margin compression below 15%"],
        "confidence": 0.85,
        "monitoring_triggers": ["Debt-to-equity ratio > 1.5"],
        "dissenting_opinion": "Bear case correctly highlights currency risk.",
        "chat_response": "MAD Finance CIO\nInvestment decision · DANGCEM\n\nBuy\n\nOpening assessment: Strong growth prospects support our investment thesis.\nWhat makes the investment attractive:\n- Revenue growth accelerating\nWhat makes me cautious:\n- FX volatility\nOne issue I couldn't ignore:\n- Regulatory changes\nMy investment decision:\nAllocate with confidence.\nProposed allocation: ₦5,000,000\nProposed shares: 15,000\nModel confidence: 85%\nDecision: Buy\nWhat would change my mind:\n- Margin compression.\nMy conclusion: Solid investment case."
    }
    resp = ArbitratorResponse(**data)
    assert resp.verdict == "BUY"
    assert resp.confidence == 0.85
    assert len(resp.chat_response) >= 100

    with pytest.raises(Exception):
        ArbitratorResponse(**{**data, "verdict": "MAYBE"})

    with pytest.raises(Exception):
        ArbitratorResponse(**{**data, "rationale": "Too short"})

    with pytest.raises(Exception):
        ArbitratorResponse(**{**data, "chat_response": "Too short"})


def test_remove_price_fallback():
    """Test that missing or invalid current_price raises ValueError (no ₦100 fallback)."""
    with pytest.raises(ValueError, match="current_price is required"):
        _calculate_recommendation(
            verdict="BUY",
            confidence=0.9,
            capital=10_000_000.0,
            risk_tolerance="Moderate",
            current_price=None
        )

    with pytest.raises(ValueError, match="current_price is required"):
        _calculate_recommendation(
            verdict="BUY",
            confidence=0.9,
            capital=10_000_000.0,
            risk_tolerance="Moderate",
            current_price=0.0
        )


def test_normalize_risk_tolerance():
    """Test risk tolerance normalization and invalid input rejection."""
    rec1 = _calculate_recommendation(
        verdict="BUY",
        confidence=0.9,
        capital=10_000_000.0,
        risk_tolerance="  conservative  ",
        current_price=200.0
    )
    assert rec1["position_size"] > 0

    with pytest.raises(ValueError, match="Invalid risk tolerance"):
        _calculate_recommendation(
            verdict="BUY",
            confidence=0.9,
            capital=10_000_000.0,
            risk_tolerance="YoloRisk",
            current_price=200.0
        )


def test_market_price_freshness():
    """Test market price freshness validation with timestamps."""
    fresh_time = datetime.now(timezone.utc) - timedelta(hours=12)
    stale_time = datetime.now(timezone.utc) - timedelta(hours=80)

    # Fresh price should succeed
    rec = _calculate_recommendation(
        verdict="BUY",
        confidence=0.9,
        capital=10_000_000.0,
        risk_tolerance="Moderate",
        current_price=200.0,
        price_timestamp=fresh_time
    )
    assert rec["position_size"] > 0

    # Stale price (> 72h) should raise ValueError
    with pytest.raises(ValueError, match="Market price is stale"):
        _calculate_recommendation(
            verdict="BUY",
            confidence=0.9,
            capital=10_000_000.0,
            risk_tolerance="Moderate",
            current_price=200.0,
            price_timestamp=stale_time
        )


def test_calculate_recommendation():
    """Test deterministic risk-based recommendation calculation."""
    capital = 10_000_000.0
    current_price = 200.0

    rec = _calculate_recommendation(
        verdict="BUY",
        confidence=0.9,
        capital=capital,
        risk_tolerance="Moderate",
        current_price=current_price
    )
    assert rec["stop_loss"] < current_price
    assert rec["target_price"] > current_price
    assert rec["confidence"] == 0.9
    assert rec["position_size"] > 0
    assert rec["allocation"] > 0


@pytest.mark.asyncio
async def test_dcf_model_validation():
    """Test that invalid DCF inputs and missing units/values are rejected."""
    # Valid DCF call via ainvoke
    res = await run_dcf_model.ainvoke({
        "fcf": 100.0,
        "growth_rate": 0.10,
        "wacc": 0.15,
        "terminal_growth": 0.03,
        "years": 5
    })
    assert "intrinsic_value_millions" in res

    # Invalid FCF (<= 0 or non-numeric)
    with pytest.raises(Exception):
        await run_dcf_model.ainvoke({
            "fcf": -10.0,
            "growth_rate": 0.10,
            "wacc": 0.15,
            "terminal_growth": 0.03,
        })

    # Invalid WACC <= terminal_growth
    with pytest.raises(Exception):
        await run_dcf_model.ainvoke({
            "fcf": 100.0,
            "growth_rate": 0.10,
            "wacc": 0.02,
            "terminal_growth": 0.03,
        })


@pytest.mark.asyncio
async def test_arbitrator_node_enforces_structured_output():
    """Test that LangGraphDebateEngine._arbitrator invokes with_structured_output and returns structured verdict."""
    mock_llm_client = MagicMock()
    mock_chat_model = MagicMock()
    mock_llm_client.get_chat_model.return_value = mock_chat_model

    mock_structured_llm = AsyncMock()
    valid_resp = ArbitratorResponse(
        verdict="BUY",
        investment_thesis="Strong fundamentals and compelling valuation warrant capital allocation.",
        valuation_assessment="Attractive P/E relative to growth rate.",
        time_horizon="6-12 months",
        rationale="Clear margin of safety and solid execution track record from management.",
        bull_arguments_accepted=["Robust revenue growth"],
        bear_arguments_accepted=["Supply chain costs"],
        unresolved_risks=["Inflation headwinds"],
        conditions_that_would_change_verdict=["Revenue decline for two consecutive quarters"],
        confidence=0.8,
        monitoring_triggers=["Inflation rate > 20%"],
        dissenting_opinion="None",
        chat_response="MAD Finance CIO\nInvestment decision · DANGCEM\n\nBuy\n\nOpening assessment: Strong fundamentals support the investment case.\nWhat makes the investment attractive:\n- Robust revenue growth\nWhat makes me cautious:\n- Supply chain costs\nOne issue I couldn't ignore:\n- Inflation headwinds\nMy investment decision:\nAllocate funds safely.\nProposed allocation: ₦8,000,000\nProposed shares: 26,666\nModel confidence: 80%\nDecision: Buy\nWhat would change my mind:\n- Revenue decline.\nMy conclusion: Convincing buy case."
    )
    mock_structured_llm.ainvoke.return_value = valid_resp
    mock_chat_model.with_structured_output.return_value = mock_structured_llm

    mock_bind_tools = MagicMock()
    mock_bind_tools.ainvoke = AsyncMock(return_value=MagicMock(content="Done", tool_calls=None))
    mock_chat_model.bind_tools.return_value = mock_bind_tools

    engine = LangGraphDebateEngine(llm_client=mock_llm_client)

    state = {
        "ticker": "DANGCEM",
        "company_name": "Dangote Cement",
        "bull_case_outputs": ["Bull argument 1"],
        "bear_case_outputs": ["Bear argument 1"],
        "capital": 10_000_000.0,
        "risk_tolerance": "Moderate",
        "current_price": 300.0,
        "financial_context": []
    }

    result = await engine._arbitrator(state)

    assert result["verdict"] == "BUY"
    assert result["recommendation"]["allocation"] > 0
    assert "arbitrator_output" in result

    parsed = json.loads(result["arbitrator_output"])
    assert parsed["verdict"] == "BUY"
    assert parsed["confidence"] == 0.8
    assert "chat_response" in parsed
    mock_chat_model.with_structured_output.assert_called_once_with(ArbitratorResponse)
