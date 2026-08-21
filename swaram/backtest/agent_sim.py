from typing import Any, Dict, List
from swaram.backtest.engine import BacktestEngine
from swaram.core.symbols import resolve_canonical


class AgentBacktestSimulator:
    """Wrapper to intercept agent tool calling execution and route requests to backtest simulation environment."""

    def __init__(self, engine: BacktestEngine):
        self.engine = engine
        self.orders: List[Dict[str, Any]] = []

    def intercept_place_order(self, symbol: str, side: str, quantity: float, current_price: float, timestamp: Any) -> Dict[str, Any]:
        """Intercept live order submission and route to historical backtest match engine."""
        trade = self.engine.execute_market_order(
            side=side,
            qty=quantity,
            current_price=current_price,
            timestamp=timestamp,
        )
        sim_id = f"sim_{len(self.orders) + 1}"
        order_res = {
            "id": sim_id,
            "symbol": symbol,
            "side": side.lower(),
            "size": int(quantity),
            "order_type": "market",
            "state": "filled",
            "average_fill_price": str(trade["price"]),
        }
        self.orders.append(order_res)
        return order_res

    def intercept_get_account_state(self, current_price: float) -> Dict[str, Any]:
        """Intercept account query and return historical backtest capital state."""
        equity = self.engine.cash + (self.engine.position * current_price)
        return {
            "balances": [
                {
                    "asset": "USDT",
                    "balance": f"{self.engine.cash:.2f}",
                    "equity": f"{equity:.2f}",
                    "available_margin": f"{self.engine.cash:.2f}",
                }
            ],
            "positions": [
                {
                    "symbol": "BTCUSD",
                    "size": str(self.engine.position),
                    "entry_price": f"{self.engine.entry_price:.2f}",
                }
            ] if self.engine.position != 0 else [],
        }
