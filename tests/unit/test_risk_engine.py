import pytest
from swaram.risk.engine import RiskEngine, RiskState


def test_risk_drawdown_limit():
    engine = RiskEngine()
    state = RiskState(
        current_capital=8500.0,    # 15% drawdown
        initial_capital=10000.0,
        position_size=0.0,
        entry_price=60000.0,
        current_price=60000.0,
        max_drawdown_pct=10.0,
        max_position_pct=20.0,
        max_loss_per_trade_pct=2.0,
    )
    res = engine.check_trade(state, 0.1)
    assert not res.allowed
    assert "drawdown" in res.reason


def test_risk_position_limit():
    engine = RiskEngine()
    state = RiskState(
        current_capital=10000.0,
        initial_capital=10000.0,
        position_size=0.0,
        entry_price=60000.0,
        current_price=60000.0,
        max_drawdown_pct=10.0,
        max_position_pct=20.0,      # limit is $2000 exposure
        max_loss_per_trade_pct=2.0,
    )
    # Requested trade value = 0.05 * 60000 = 3000 (exceeds $2000 limit)
    res = engine.check_trade(state, 0.05)
    assert not res.allowed
    assert "exposure" in res.reason or "limit" in res.reason


def test_kelly_sizing():
    engine = RiskEngine()
    # 55% win rate, win/loss odds = 2:1
    qty = engine.kelly_size(
        win_rate=0.55,
        avg_win=200.0,
        avg_loss=100.0,
        capital=10000.0,
        current_price=60000.0,
        fraction=0.25,
    )
    assert qty >= 0.0
