import pytest
from swaram.agents.strategy import StrategyContext, MomentumStrategy, MeanReversionStrategy, TradeSignal


def test_momentum_strategy_buy():
    strat = MomentumStrategy(rsi_buy_threshold=35.0)
    ctx = StrategyContext(
        symbol="BTCUSD",
        last_price=60000.0,
        rsi=30.0,
        macd=0.0,
        macd_signal=0.0,
        ema_9=59000.0,
        ema_21=58000.0,
        vwap=59500.0,
        bollinger_upper=62000.0,
        bollinger_lower=58000.0,
        current_position=0.0,
        current_capital=10000.0,
    )
    decision = strat.decide(ctx)
    assert decision["signal"] == TradeSignal.BUY
    assert decision["quantity"] > 0.0


def test_momentum_strategy_sell():
    strat = MomentumStrategy(rsi_sell_threshold=65.0)
    ctx = StrategyContext(
        symbol="BTCUSD",
        last_price=60000.0,
        rsi=70.0,
        macd=0.0,
        macd_signal=0.0,
        ema_9=59000.0,
        ema_21=58000.0,
        vwap=59500.0,
        bollinger_upper=62000.0,
        bollinger_lower=58000.0,
        current_position=0.1,
        current_capital=4000.0,
    )
    decision = strat.decide(ctx)
    assert decision["signal"] == TradeSignal.SELL
    assert decision["quantity"] == 0.1


def test_mean_reversion_strategy_buy():
    strat = MeanReversionStrategy()
    ctx = StrategyContext(
        symbol="BTCUSD",
        last_price=57500.0,
        rsi=28.0,
        macd=0.0,
        macd_signal=0.0,
        ema_9=59000.0,
        ema_21=58000.0,
        vwap=59500.0,
        bollinger_upper=62000.0,
        bollinger_lower=58000.0,
        current_position=0.0,
        current_capital=10000.0,
    )
    decision = strat.decide(ctx)
    assert decision["signal"] == TradeSignal.BUY
