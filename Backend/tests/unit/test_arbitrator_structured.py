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
from src.domain.services.report_validator import ReportConsistencyValidator


def test_arbitrator_response_validation():
    """Test Pydantic validation for ArbitratorResponse prose-first 8-section schema including chat_response."""
    long_prose = "This is a detailed narrative prose paragraph that exceeds one hundred characters to satisfy Pydantic min_length validation rules for the investment report section."
    long_thesis = "This is a detailed narrative prose paragraph that exceeds one hundred and fifty characters to satisfy Pydantic min_length validation rules for the comprehensive investment thesis section covering financial performance, valuation, and competitive advantage."

    data = {
        "ticker": "DANGCEM",
        "company_name": "Dangote Cement Plc",
        "exchange": "NGX",
        "current_market_price": 300.0,
        "verdict": "Buy",
        "investment_horizon": "12 months",
        "confidence_score": 0.85,
        "section_1_verdict_prose": long_prose,
        "section_2_thesis_prose": long_thesis,
        "section_3_risks_prose": long_prose,
        "section_4_plan_prose": long_prose,
        "section_5_performance_prose": long_prose,
        "section_6_exit_prose": long_prose,
        "section_7_monitoring_prose": long_prose,
        "section_8_conclusion_prose": long_prose,
        "recommendation": {
            "verdict": "Buy",
            "available_capital": 10_000_000.0,
            "proposed_allocation": 5_000_000.0,
            "allocation_percentage": 50.0,
            "share_quantity": 16583,
            "entry_price": 300.0,
            "stop_loss": 255.0,
            "target_price": 390.0,
            "transaction_costs": 25000.0,
            "remaining_cash": 4_975_000.0,
            "scenarios": []
        },
        "chat_response": "# MAD Finance CIO Investment Decision Report\n\n## 1. Investment Verdict\nDangote Cement Plc (DANGCEM) - Buy.\n\n## 2. Investment Thesis\nStrong market position and revenue growth.\n\n## 3. Investment Risks\nFX volatility and energy costs.\n\n## 4. Recommended Investment Plan\nAllocate ₦5,000,000 (16,666 shares).\n\n## 5. Expected Investment Performance\nFavorable return scenarios.\n\n## 6. Exit Strategy\nTake profits above target price.\n\n## 7. What to Monitor\nOperating margins and revenue growth.\n\n## 8. Final CIO Conclusion\nBuy recommendation." * 3
    }
    resp = ArbitratorResponse(**data)
    assert resp.verdict == "Buy"
    assert resp.confidence_score == 0.85
    assert len(resp.chat_response) >= 300

    errors = ReportConsistencyValidator.validate(resp)
    assert len(errors) == 0

    with pytest.raises(Exception):
        ArbitratorResponse(**{**data, "verdict": "Maybe"})


def test_report_consistency_validator():
    """Test that ReportConsistencyValidator catches verdict-action mismatches and cash reconciliation errors."""
    long_prose = "This is a detailed narrative prose paragraph that exceeds one hundred characters to satisfy Pydantic min_length validation rules for the investment report section."
    long_thesis = "This is a detailed narrative prose paragraph that exceeds one hundred and fifty characters to satisfy Pydantic min_length validation rules for the comprehensive investment thesis section covering financial performance, valuation, and competitive advantage."

    rep = ArbitratorResponse(
        ticker="DANGCEM",
        company_name="Dangote Cement",
        current_market_price=300.0,
        verdict="Sell",
        investment_horizon="12 months",
        confidence_score=0.9,
        section_1_verdict_prose=long_prose,
        section_2_thesis_prose=long_thesis,
        section_3_risks_prose=long_prose,
        section_4_plan_prose=long_prose,
        section_5_performance_prose=long_prose,
        section_6_exit_prose=long_prose,
        section_7_monitoring_prose=long_prose,
        section_8_conclusion_prose=long_prose,
        recommendation={
            "verdict": "Sell",
            "available_capital": 10_000_000.0,
            "proposed_allocation": 5_000_000.0,  # Error: Sell shouldn't allocate capital
            "allocation_percentage": 50.0,
            "share_quantity": 1000,
            "entry_price": 300.0,
            "transaction_costs": 10000.0,
            "remaining_cash": 4_990_000.0,
            "scenarios": []
        },
        chat_response="Full prose report " * 25
    )
    errors = ReportConsistencyValidator.validate(rep)
    assert len(errors) > 0
    assert any("Sell" in err for err in errors)


def test_remove_price_fallback():
    """Test that missing or invalid current_price raises ValueError (no ₦100 fallback)."""
    with pytest.raises(ValueError, match="current_price is required"):
        _calculate_recommendation(
            verdict="Buy",
            confidence=0.9,
            capital=10_000_000.0,
            risk_tolerance="Moderate",
            current_price=None
        )

    with pytest.raises(ValueError, match="current_price is required"):
        _calculate_recommendation(
            verdict="Buy",
            confidence=0.9,
            capital=10_000_000.0,
            risk_tolerance="Moderate",
            current_price=0.0
        )


def test_normalize_risk_tolerance():
    """Test risk tolerance normalization and invalid input rejection."""
    rec1 = _calculate_recommendation(
        verdict="Buy",
        confidence=0.9,
        capital=10_000_000.0,
        risk_tolerance="  conservative  ",
        current_price=200.0
    )
    assert rec1["position_size"] > 0

    with pytest.raises(ValueError, match="Invalid risk tolerance"):
        _calculate_recommendation(
            verdict="Buy",
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
        verdict="Buy",
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
            verdict="Buy",
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
        verdict="Buy",
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
    res = await run_dcf_model.ainvoke({
        "fcf": 100.0,
        "growth_rate": 0.10,
        "wacc": 0.15,
        "terminal_growth": 0.03,
        "years": 5
    })
    assert "intrinsic_value_millions" in res

    with pytest.raises(Exception):
        await run_dcf_model.ainvoke({
            "fcf": -10.0,
            "growth_rate": 0.10,
            "wacc": 0.15,
            "terminal_growth": 0.03,
        })

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

    long_prose = "This is a detailed narrative prose paragraph that exceeds one hundred characters to satisfy Pydantic min_length validation rules for the investment report section."
    long_thesis = "This is a detailed narrative prose paragraph that exceeds one hundred and fifty characters to satisfy Pydantic min_length validation rules for the comprehensive investment thesis section covering financial performance, valuation, and competitive advantage."

    mock_structured_llm = AsyncMock()
    valid_resp = ArbitratorResponse(
        ticker="DANGCEM",
        company_name="Dangote Cement Plc",
        exchange="NGX",
        current_market_price=300.0,
        verdict="Buy",
        investment_horizon="12 months",
        confidence_score=0.8,
        section_1_verdict_prose=long_prose,
        section_2_thesis_prose=long_thesis,
        section_3_risks_prose=long_prose,
        section_4_plan_prose=long_prose,
        section_5_performance_prose=long_prose,
        section_6_exit_prose=long_prose,
        section_7_monitoring_prose=long_prose,
        section_8_conclusion_prose=long_prose,
        recommendation={
            "verdict": "Buy",
            "available_capital": 10_000_000.0,
            "proposed_allocation": 8_000_000.0,
            "allocation_percentage": 80.0,
            "share_quantity": 26666,
            "entry_price": 300.0,
            "stop_loss": 255.0,
            "target_price": 390.0,
            "transaction_costs": 40000.0,
            "remaining_cash": 1960000.0,
            "scenarios": []
        },
        chat_response="# MAD Finance CIO Investment Decision Report\n\n## 1. Investment Verdict\nDangote Cement Plc (DANGCEM) - Buy.\n\n## 2. Investment Thesis\nStrong market position and revenue growth.\n\n## 3. Investment Risks\nFX volatility and energy costs.\n\n## 4. Recommended Investment Plan\nAllocate ₦8,000,000 (26,666 shares).\n\n## 5. Expected Investment Performance\nFavorable return scenarios.\n\n## 6. Exit Strategy\nTake profits above target price.\n\n## 7. What to Monitor\nOperating margins and revenue growth.\n\n## 8. Final CIO Conclusion\nBuy recommendation." * 3
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

    assert result["verdict"] == "Buy"
    assert result["recommendation"]["allocation"] > 0
    assert "arbitrator_output" in result
    assert result["chat_response"] == valid_resp.chat_response

    parsed = json.loads(result["arbitrator_output"])
    assert parsed["verdict"] == "Buy"
    assert parsed["confidence_score"] == 0.8
    assert "chat_response" in parsed
    mock_chat_model.with_structured_output.assert_called_once_with(ArbitratorResponse)
