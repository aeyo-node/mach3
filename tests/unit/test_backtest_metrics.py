import numpy as np
import pytest
from datetime import datetime, timezone
from swaram.backtest.engine import BacktestEngine


@pytest.fixture
def engine():
    return BacktestEngine(initial_capital=10000.0, slippage_pct=0.05)


def ts():
    return datetime.now(timezone.utc)


def test_sharpe_zero_on_no_trades(engine):
    metrics = engine.calculate_performance_metrics()
    assert metrics["total_trades"] == 0
    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["max_drawdown"] == 0.0


def test_buy_then_sell(engine):
    engine.execute_market_order("buy", 0.1, 65000.0, ts())
    engine.update_portfolio(65000.0)
    engine.execute_market_order("sell", 0.1, 66000.0, ts())
    engine.update_portfolio(66000.0)

    metrics = engine.calculate_performance_metrics()
    assert metrics["total_trades"] == 2
    assert metrics["win_rate"] == 100.0
    assert metrics["profit_factor"] > 1.0


def test_max_drawdown(engine):
    engine.equity_curve = [10000.0, 9000.0, 8000.0, 9500.0]
    engine.returns = [0.0, -0.1, -0.11, 0.1875]

    metrics = engine.calculate_performance_metrics()
    assert metrics["max_drawdown"] > 0.0


def test_equity_curve_grows_on_gain(engine):
    engine.execute_market_order("buy", 1.0, 100.0, ts())
    engine.update_portfolio(110.0)  # price went up

    assert engine.equity_curve[-1] > engine.initial_capital
