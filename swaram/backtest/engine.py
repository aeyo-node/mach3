import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional


class BacktestEngine:
    """Historical market data event-driven backtesting simulator."""

    def __init__(self, initial_capital: float = 10000.0, slippage_pct: float = 0.05):
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct / 100.0

        self.cash = initial_capital
        self.position = 0.0  # Number of contracts / assets held
        self.entry_price = 0.0
        self.equity_curve: List[float] = [initial_capital]
        self.returns: List[float] = []
        self.trades: List[Dict[str, Any]] = []

    def execute_market_order(self, side: str, qty: float, current_price: float, timestamp: datetime) -> Dict[str, Any]:
        """Simulate immediate market order execution with slippage."""
        side = side.lower()
        slippage = current_price * self.slippage_pct
        fill_price = current_price + slippage if side == "buy" else current_price - slippage

        cost = qty * fill_price

        if side == "buy":
            # Long entry / Cover short
            self.cash -= cost
            self.position += qty
            self.entry_price = fill_price
        else:
            # Short entry / Close long
            self.cash += cost
            self.position -= qty
            self.entry_price = fill_price

        trade = {
            "timestamp": timestamp,
            "side": side,
            "quantity": qty,
            "price": fill_price,
            "value": cost,
        }
        self.trades.append(trade)
        return trade

    def update_portfolio(self, current_price: float) -> float:
        """Update current portfolio value and equity curve."""
        asset_value = self.position * current_price
        portfolio_value = self.cash + asset_value
        
        prev_equity = self.equity_curve[-1]
        self.equity_curve.append(portfolio_value)
        
        ret = (portfolio_value - prev_equity) / prev_equity if prev_equity > 0 else 0.0
        self.returns.append(ret)
        
        return portfolio_value

    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Compute Sharpe Ratio, Max Drawdown, Profit Factor, and Win Rate."""
        total_trades = len(self.trades)
        if total_trades == 0:
            return {
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "profit_factor": 1.0,
                "win_rate": 0.0,
                "total_trades": 0,
            }

        # Win rate & Profit factor
        wins = 0
        gross_profit = 0.0
        gross_loss = 0.0

        for i in range(1, len(self.trades), 2):
            if i >= len(self.trades):
                break
            entry = self.trades[i - 1]
            exit = self.trades[i]
            pnl = (exit["price"] - entry["price"]) * entry["quantity"]
            if entry["side"] == "sell":  # Was short
                pnl = -pnl

            if pnl > 0:
                wins += 1
                gross_profit += pnl
            else:
                gross_loss += abs(pnl)

        win_rate = (wins / (total_trades // 2)) * 100.0 if total_trades >= 2 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)

        # Sharpe ratio
        daily_returns = np.array(self.returns)
        mean_ret = np.mean(daily_returns) if len(daily_returns) > 0 else 0.0
        std_ret = np.std(daily_returns) if len(daily_returns) > 0 else 0.0
        sharpe = (mean_ret / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0

        # Max drawdown
        peak = self.initial_capital
        max_dd = 0.0
        for val in self.equity_curve:
            if val > peak:
                peak = val
            dd = (peak - val) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return {
            "sharpe_ratio": float(round(sharpe, 4)),
            "max_drawdown": float(round(max_dd * 100.0, 2)),
            "profit_factor": float(round(profit_factor, 2)),
            "win_rate": float(round(win_rate, 2)),
            "total_trades": total_trades,
            "final_capital": float(round(self.equity_curve[-1], 2)),
        }
