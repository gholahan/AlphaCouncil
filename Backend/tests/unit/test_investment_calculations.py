"""Unit tests for deterministic investment calculation services."""

import pytest
from src.domain.services.investment_calculations import (
    calculate_transaction_costs,
    calculate_share_quantity,
    calculate_dividend_income,
    calculate_annualized_return,
    calculate_scenario_performance,
    calculate_entry_strategy,
)


def test_transaction_costs_ngx():
    costs = calculate_transaction_costs(1_000_000.0, "NGX")
    assert costs["sec_fee"] == 3000.0
    assert costs["nse_fee"] == 200.0
    assert costs["cscs_fee"] == 300.0
    assert costs["broker_commission"] == 13500.0
    assert costs["total_costs"] == 17000.0


def test_share_quantity():
    # Allocation 1M, price 200, costs 17k -> net 983k / 200 = 4915 shares
    shares = calculate_share_quantity(1_000_000.0, 200.0, 17000.0)
    assert shares == 4915


def test_dividend_income():
    # 1000 shares, ₦10 DPS, 2 years, 5% growth
    # Year 1: 1000 * 10 = 10,000
    # Year 2: 1000 * 10.5 = 10,500
    # Total: 20,500
    divs = calculate_dividend_income(1000, 10.0, 2, 0.05)
    assert divs == 20500.0


def test_annualized_return():
    # Start 100k, end 144k over 2 years -> (1.44)**0.5 - 1 = 20% CAGR
    cagr = calculate_annualized_return(100_000.0, 144_000.0, 2.0)
    assert cagr == 20.0


def test_scenario_performance():
    scenarios = {
        "Bear Case": 180.0,
        "Base Case": 250.0,
        "Bull Case": 300.0,
    }
    perf = calculate_scenario_performance(200.0, 1000, scenarios, 5000.0, 2.0)
    assert len(perf) == 3
    assert perf[0]["scenario_name"] == "Bear Case"
    assert perf[1]["scenario_name"] == "Base Case"
    assert perf[2]["scenario_name"] == "Bull Case"
    assert perf[1]["total_investment_value"] > 200_000.0


def test_entry_strategy():
    strat = calculate_entry_strategy(250.0, "Strong Buy")
    assert strat["entry_range_min"] < 250.0
    assert "Staged entry" in strat["execution_strategy"]
