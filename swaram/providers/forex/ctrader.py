import asyncio
import aiohttp
from typing import AsyncGenerator, Dict, List, Optional
from swaram.core.events import TickEvent
from swaram.core.health import ProviderHealth
from swaram.core.logging import get_logger
from swaram.core.symbols import to_canonical
from swaram.core.time import now_utc
from swaram.providers.base import BaseMarketDataProvider

logger = get_logger("providers.ctrader")

# Yahoo Finance symbol mapping (free, no API key required)
YAHOO_SYMBOLS: Dict[str, str] = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "USDCHF": "CHF=X",
    "AUDUSD": "AUDUSD=X",
    "XAUUSD": "GC=F",   # Gold Futures
    "XAGUSD": "SI=F",   # Silver Futures
    "WTIUSD": "CL=F",   # WTI Crude Oil Futures
    "US10Y":  "%5ETNX", # 10-Year US Treasury Yield
}

SPREADS: Dict[str, float] = {
    "EURUSD": 0.00010,
    "GBPUSD": 0.00015,
    "USDJPY": 0.015,
    "USDCHF": 0.00015,
    "AUDUSD": 0.00015,
    "XAUUSD": 0.30,
    "XAGUSD": 0.03,
    "WTIUSD": 0.05,
    "US10Y":  0.001,
}

_YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
_HEADERS = {"User-Agent": "Mozilla/5.0"}


async def _fetch_yahoo_price(session: aiohttp.ClientSession, yahoo_sym: str) -> Optional[float]:
    """Fetch latest price for a Yahoo Finance symbol."""
    url = f"{_YAHOO_BASE}/{yahoo_sym}?interval=1m&range=5m"
    try:
        async with session.get(url, headers=_HEADERS, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice") or meta.get("previousClose")
            return float(price) if price else None
    except Exception as e:
        logger.warning(f"Yahoo Finance fetch failed for {yahoo_sym}", error=str(e))
        return None


async def _fetch_all_prices(symbols: List[str]) -> Dict[str, float]:
    """Fetch all current prices from Yahoo Finance in one async pass."""
    prices: Dict[str, float] = {}
    async with aiohttp.ClientSession() as session:
        tasks = {
            sym: _fetch_yahoo_price(session, YAHOO_SYMBOLS[sym])
            for sym in symbols
            if sym in YAHOO_SYMBOLS
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for sym, result in zip(tasks.keys(), results):
            if isinstance(result, float) and result > 0:
                prices[sym] = result
    return prices


class CTraderForexProvider(BaseMarketDataProvider):
    """Forex, Metals & Commodities real-time price provider via Yahoo Finance free API."""

    def __init__(self, symbols: Optional[List[str]] = None, poll_interval: float = 5.0):
        self.symbols = symbols or list(YAHOO_SYMBOLS.keys())
        self.poll_interval = poll_interval
        self.health = ProviderHealth(provider="ctrader", stale_threshold_sec=30.0)
        self._running = False
        self._prices: Dict[str, float] = {}

    @property
    def name(self) -> str:
        return "ctrader"

    async def connect(self) -> None:
        self._running = True
        self.health.connected = True
        # Warm up: do an initial price fetch before streaming
        logger.info("CTrader/Forex provider: initial price fetch from Yahoo Finance...")
        self._prices = await _fetch_all_prices(self.symbols)
        logger.info(f"Warmed up prices for {len(self._prices)} symbols.", prices=self._prices)

    async def disconnect(self) -> None:
        self._running = False
        self.health.connected = False
        logger.info("cTrader Forex/Metals/Commodities provider disconnected.")

    async def subscribe(self, symbols: List[str], channels: Optional[List[str]] = None) -> None:
        self.symbols = symbols

    async def stream_events(self) -> AsyncGenerator[object, None]:
        """Stream real-time prices polled from Yahoo Finance every `poll_interval` seconds."""
        while self._running:
            try:
                fresh = await _fetch_all_prices(self.symbols)
                if fresh:
                    self._prices.update(fresh)

                ts = now_utc()
                for sym in self.symbols:
                    mid = self._prices.get(sym)
                    if not mid:
                        continue

                    spread = SPREADS.get(sym, 0.0001)
                    bid = round(mid - spread / 2.0, 5)
                    ask = round(mid + spread / 2.0, 5)
                    canonical = to_canonical("ctrader", sym)

                    self.health.record_message(ts)
                    yield TickEvent(
                        canonical_symbol=canonical,
                        provider="ctrader",
                        timestamp=ts,
                        bid=bid,
                        ask=ask,
                        mid=mid,
                        last=mid,
                        bid_size=1_000_000.0,
                        ask_size=1_000_000.0,
                    )

                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.health.record_error(str(e))
                logger.error("Error polling Yahoo Finance prices", error=str(e))
                await asyncio.sleep(10.0)
