"""
Swaram Strategy Runner — Autonomous agent execution loop.
Fetches live market context, evaluates strategy signals, and executes orders.
"""
import asyncio
from typing import Any, Dict, Optional
from swaram.core.logging import get_logger
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_utc, now_utc
from swaram.agents.strategy import BaseStrategy, StrategyContext, STRATEGY_REGISTRY, TradeSignal
from swaram.storage.redis import RedisLiveStore

logger = get_logger("agents.loop")

# Global state for running loops per symbol
_running_loops: Dict[str, asyncio.Task] = {}


class StrategyRunner:
    """Autonomous strategy execution loop — observe → decide → execute."""

    def __init__(
        self,
        symbol: str,
        strategy: BaseStrategy,
        redis_store: RedisLiveStore,
        interval_sec: float = 10.0,
        capital: float = 10000.0,
    ):
        self.symbol = symbol
        self.canonical = resolve_canonical(symbol)
        self.strategy = strategy
        self.redis_store = redis_store
        self.interval_sec = interval_sec
        self.capital = capital
        self.position = 0.0
        self.cycle_count = 0
        self.trade_log: list = []
        self._running = False

    async def run_once(self) -> Dict[str, Any]:
        """Execute a single strategy cycle: observe → decide → (simulate) execute."""
        snap = await self.redis_store.get_snapshot(self.canonical)
        last_price = float(snap.get("last", 0.0)) if snap else 0.0

        if last_price == 0.0:
            return {
                "cycle": self.cycle_count,
                "timestamp_utc": iso_utc(now_utc()),
                "signal": TradeSignal.NONE,
                "reason": "No live price available",
            }

        # Build strategy context from live snapshot
        ctx = StrategyContext(
            symbol=self.symbol,
            last_price=last_price,
            rsi=snap.get("rsi") if snap else None,
            macd=snap.get("macd") if snap else None,
            macd_signal=snap.get("macd_signal") if snap else None,
            ema_9=snap.get("ema_9") if snap else None,
            ema_21=snap.get("ema_21") if snap else None,
            vwap=snap.get("vwap") if snap else None,
            bollinger_upper=snap.get("bollinger_upper") if snap else None,
            bollinger_lower=snap.get("bollinger_lower") if snap else None,
            current_position=self.position,
            current_capital=self.capital,
        )

        decision = self.strategy.decide(ctx)
        self.cycle_count += 1

        signal = decision.get("signal", TradeSignal.NONE)
        qty = decision.get("quantity", 0.0)

        # Simulated execution (Phase 10 uses simulation; Phase 7 client for live)
        if signal == TradeSignal.BUY and qty > 0:
            cost = qty * last_price
            self.capital -= cost
            self.position += qty
            logger.info(f"[{self.symbol}] BUY {qty} @ {last_price:.2f}", strategy=self.strategy.name)

        elif signal in (TradeSignal.SELL, TradeSignal.CLOSE) and qty > 0:
            proceeds = qty * last_price
            self.capital += proceeds
            self.position = max(0.0, self.position - qty)
            logger.info(f"[{self.symbol}] SELL {qty} @ {last_price:.2f}", strategy=self.strategy.name)

        result = {
            "cycle": self.cycle_count,
            "timestamp_utc": iso_utc(now_utc()),
            "strategy": self.strategy.name,
            "symbol": self.symbol,
            "last_price": last_price,
            "signal": signal,
            "quantity": qty,
            "reason": decision.get("reason", ""),
            "position_after": self.position,
            "capital_after": round(self.capital, 2),
        }
        self.trade_log.append(result)
        return result

    async def _loop(self) -> None:
        self._running = True
        logger.info(f"StrategyRunner started", symbol=self.symbol, strategy=self.strategy.name)
        try:
            while self._running:
                await self.run_once()
                await asyncio.sleep(self.interval_sec)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            logger.info(f"StrategyRunner stopped", symbol=self.symbol)

    def start(self) -> None:
        task = asyncio.create_task(self._loop())
        _running_loops[self.symbol] = task

    def stop(self) -> None:
        self._running = False
        task = _running_loops.pop(self.symbol, None)
        if task:
            task.cancel()

    def status(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy.name,
            "running": self._running,
            "cycle_count": self.cycle_count,
            "position": self.position,
            "capital": round(self.capital, 2),
            "last_trades": self.trade_log[-5:],
        }


# Global registry of active runners (keyed by symbol)
_active_runners: Dict[str, StrategyRunner] = {}


def get_runner(symbol: str) -> Optional[StrategyRunner]:
    return _active_runners.get(symbol)


def set_runner(symbol: str, runner: StrategyRunner) -> None:
    _active_runners[symbol] = runner


def remove_runner(symbol: str) -> None:
    _active_runners.pop(symbol, None)
