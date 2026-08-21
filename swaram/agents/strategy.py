"""
Swaram Strategy Framework.

Defines the BaseStrategy abstract class and two built-in rule-based strategies:
  - MomentumStrategy: RSI + VWAP trend-following.
  - MeanReversionStrategy: Price deviation from VWAP.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class TradeSignal:
    NONE = "none"
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"


class StrategyContext:
    """Normalized market state passed into every strategy decision call."""

    def __init__(
        self,
        symbol: str,
        last_price: float,
        rsi: Optional[float],
        macd: Optional[float],
        macd_signal: Optional[float],
        ema_9: Optional[float],
        ema_21: Optional[float],
        vwap: Optional[float],
        bollinger_upper: Optional[float],
        bollinger_lower: Optional[float],
        current_position: float = 0.0,
        current_capital: float = 10000.0,
    ):
        self.symbol = symbol
        self.last_price = last_price
        self.rsi = rsi
        self.macd = macd
        self.macd_signal = macd_signal
        self.ema_9 = ema_9
        self.ema_21 = ema_21
        self.vwap = vwap
        self.bollinger_upper = bollinger_upper
        self.bollinger_lower = bollinger_lower
        self.current_position = current_position
        self.current_capital = current_capital


class BaseStrategy(ABC):
    """Abstract base class for all Swaram trading strategies."""

    name: str = "base"

    @abstractmethod
    def decide(self, ctx: StrategyContext) -> Dict[str, Any]:
        """
        Evaluate market context and return a trade decision.
        Returns:
            {
                "signal": "buy" | "sell" | "close" | "none",
                "quantity": float,
                "reason": str,
            }
        """
        ...


class MomentumStrategy(BaseStrategy):
    """
    RSI + VWAP momentum-following strategy.
    - Buy when: RSI < 35 (oversold) AND price above VWAP (bullish bias)
    - Sell/Close when: RSI > 65 (overbought) OR price crosses below EMA9
    """

    name = "momentum"

    def __init__(self, rsi_buy_threshold: float = 35.0, rsi_sell_threshold: float = 65.0):
        self.rsi_buy_threshold = rsi_buy_threshold
        self.rsi_sell_threshold = rsi_sell_threshold

    def decide(self, ctx: StrategyContext) -> Dict[str, Any]:
        if ctx.rsi is None or ctx.vwap is None:
            return {"signal": TradeSignal.NONE, "quantity": 0.0, "reason": "Insufficient indicators"}

        has_position = ctx.current_position > 0
        qty = round(ctx.current_capital * 0.02 / ctx.last_price, 4)  # 2% of capital

        # Entry: oversold + price above VWAP
        if not has_position and ctx.rsi < self.rsi_buy_threshold and ctx.last_price > ctx.vwap:
            return {
                "signal": TradeSignal.BUY,
                "quantity": qty,
                "reason": f"RSI {ctx.rsi:.1f} < {self.rsi_buy_threshold} (oversold) + price {ctx.last_price:.2f} > VWAP {ctx.vwap:.2f}",
            }

        # Exit: overbought
        if has_position and ctx.rsi > self.rsi_sell_threshold:
            return {
                "signal": TradeSignal.SELL,
                "quantity": ctx.current_position,
                "reason": f"RSI {ctx.rsi:.1f} > {self.rsi_sell_threshold} (overbought) — exiting long",
            }

        return {"signal": TradeSignal.NONE, "quantity": 0.0, "reason": "No signal"}


class MeanReversionStrategy(BaseStrategy):
    """
    Bollinger Band mean reversion strategy.
    - Buy when: price touches lower Bollinger Band (oversold extremes)
    - Sell when: price crosses back above the midline (VWAP or EMA21)
    """

    name = "mean_reversion"

    def decide(self, ctx: StrategyContext) -> Dict[str, Any]:
        if ctx.bollinger_lower is None or ctx.bollinger_upper is None:
            return {"signal": TradeSignal.NONE, "quantity": 0.0, "reason": "Insufficient indicators"}

        has_position = ctx.current_position > 0
        qty = round(ctx.current_capital * 0.02 / ctx.last_price, 4)

        # Entry: price touches or breaks below lower band
        if not has_position and ctx.last_price <= ctx.bollinger_lower:
            return {
                "signal": TradeSignal.BUY,
                "quantity": qty,
                "reason": f"Price {ctx.last_price:.2f} touched lower BB {ctx.bollinger_lower:.2f} — mean reversion long",
            }

        # Exit: price recovers to midline or upper band
        mid = ctx.vwap or ctx.ema_21
        if has_position and mid and ctx.last_price >= mid:
            return {
                "signal": TradeSignal.SELL,
                "quantity": ctx.current_position,
                "reason": f"Price {ctx.last_price:.2f} recovered to midline {mid:.2f} — exiting",
            }

        return {"signal": TradeSignal.NONE, "quantity": 0.0, "reason": "No signal"}


STRATEGY_REGISTRY: Dict[str, BaseStrategy] = {
    "momentum": MomentumStrategy(),
    "mean_reversion": MeanReversionStrategy(),
}
