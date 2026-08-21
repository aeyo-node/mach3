from swaram.analytics.positioning import (
    analyze_positioning,
    calculate_annualized_funding_yield,
    evaluate_positioning_regime,
)


def test_calculate_annualized_funding_yield():
    # 0.01% per 8h = 0.0001 * 3 * 365 * 100 = 10.95% APR
    yield_pct = calculate_annualized_funding_yield(0.0001)
    assert round(yield_pct, 2) == 10.95


def test_evaluate_positioning_regime():
    assert evaluate_positioning_regime(2.0, 5.0) == "AGGRESSIVE_LONG_BUILDING"
    assert evaluate_positioning_regime(-2.0, 5.0) == "AGGRESSIVE_SHORT_BUILDING"
    assert evaluate_positioning_regime(2.0, -5.0) == "SHORT_COVERING"
    assert evaluate_positioning_regime(-2.0, -5.0) == "LONG_LIQUIDATION"


def test_analyze_positioning():
    res = analyze_positioning(
        funding_rate=0.0001,
        open_interest=10000.0,
        open_interest_24h_ago=9000.0,
        price_24h_change_pct=3.5,
    )

    assert res.funding_rate == 0.0001
    assert res.annualized_yield_pct == 10.95
    assert res.positioning_regime == "AGGRESSIVE_LONG_BUILDING"
    assert res.extreme_funding_warning is False
