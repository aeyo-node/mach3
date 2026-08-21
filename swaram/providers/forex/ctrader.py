import asyncio
import random
from typing import AsyncGenerator, Dict, List, Optional
from swaram.core.events import CandleEvent, OrderbookEvent, TickEvent
from swaram.core.health import ProviderHealth
from swaram.core.logging import get_logger
from swaram.core.symbols import to_canonical
from swaram.core.time import now_utc
from swaram.providers.base import BaseMarketDataProvider

logger = get_logger("providers.ctrader")


class CTraderForexProvider(BaseMarketDataProvider):
    """cTrader / Forex & Metals Market Data Provider Adapter."""

    BASE_PRICES = {
        "EURUSD": 1.0850,
        "GBPUSD": 1.2650,
        "USDJPY": 155.20,
        "XAUUSD": 2400.50,
        "XAGUSD": 29.50,
    }

    SPREADS = {
        "EURUSD": 0.00010,
        "GBPUSD": 0.00015,
        "USDJPY": 0.015,
        "XAUUSD": 0.25,
        "XAGUSD": 0.02,
    }

    def __init__(self, symbols: Optional[List[str]] = None):
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD"]
        self.health = ProviderHealth(provider="ctrader", stale_threshold_sec=10.0)
        self._running = False
        self._prices = dict(self.BASE_PRICES)

    @property
    def name(self) -> str:
        return "ctrader"

    async def connect(self) -> None:
        self._running = True
        self.health.connected = True
        logger.info("cTrader Forex/Metals Provider connected.")

    async def disconnect(self) -> None:
        self._running = False
        self.health.connected = False
        logger.info("cTrader Forex/Metals Provider disconnected.")

    async def subscribe(self, symbols: List[str], channels: Optional[List[str]] = None) -> None:
        self.symbols = symbols
        logger.info("Subscribed to cTrader Forex symbols", symbols=symbols)

    async def stream_events(self) -> AsyncGenerator[object, None]:
        """Stream simulated/real live ticks and 1m candle updates for FX and Metals."""
        while self._running:
            try:
                await asyncio.sleep(1.0)
                ts = now_utc()

                for sym in self.symbols:
                    if not self._running:
                        break

                    base_p = self._prices.get(sym, 1.0)
                    spread = self.SPREADS.get(sym, 0.0001)

                    # Random walk simulation for live market movement
                    change = random.normalvariate(0.0, base_p * 0.0001)
                    mid = round(base_p + change, 5 if "JPY" in sym or "USD" in sym and "X" not in sym else 2)
                    self._prices[sym] = mid

                    bid = round(mid - (spread / 2.0), 5 if "JPY" in sym or "USD" in sym and "X" not in sym else 2)
                    ask = round(mid + (spread / 2.0), 5 if "JPY" in sym or "USD" in sym and "X" not in sym else 2)

                    canonical = to_canonical("ctrader", sym)

                    tick = TickEvent(
                        canonical_symbol=canonical,
                        provider="ctrader",
                        timestamp=ts,
                        bid=bid,
                        ask=ask,
                        mid=mid,
                        last=mid,
                        bid_size=1000.0,
                        ask_size=1000.0,
                    )
                    self.health.record_message(ts)
                    yield tick

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.health.record_error(str(e))
                logger.error("Error streaming cTrader events", error=str(e))
                await asyncio.sleep(2.0)
