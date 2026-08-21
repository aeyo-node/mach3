import asyncio
import signal
from typing import Dict, List, Optional
from swaram.config.settings import get_settings
from swaram.core.events import (
    CandleEvent,
    FundingEvent,
    MarkSpotPriceEvent,
    OrderbookEvent,
    TickEvent,
    TradeEvent,
)
from swaram.core.logging import get_logger, setup_logging
from swaram.models.market_data import (
    Candle,
    FundingRate,
    OrderbookSnapshot,
    Tick,
    Trade,
)
from swaram.providers.crypto.delta_ws import DeltaWebSocketProvider
from swaram.storage.postgres import close_db, get_db_session, init_db
from swaram.storage.redis import RedisLiveStore, close_redis, get_redis
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository
from swaram.storage.seed import seed_instruments

logger = get_logger("collector.delta")


class DeltaCollectorRunner:
    def __init__(self):
        self.settings = get_settings()
        self.provider = DeltaWebSocketProvider(
            ws_url=self.settings.delta_ws_url,
            symbols=self.settings.delta_symbols,
            heartbeat_interval_sec=self.settings.delta_heartbeat_sec,
            stale_threshold_sec=self.settings.delta_stale_threshold_sec,
        )
        self.redis_store = RedisLiveStore(get_redis())
        self.instrument_map: Dict[str, int] = {}  # canonical -> instrument_id
        self._running = False

        # Write buffers
        self._ticks_buf: List[Tick] = []
        self._trades_buf: List[Trade] = []
        self._candles_buf: List[Candle] = []
        self._orderbook_buf: List[OrderbookSnapshot] = []
        self._funding_buf: List[FundingRate] = []

    async def initialize(self) -> None:
        logger.info("Initializing Delta Collector Runner...")
        await init_db()
        await seed_instruments()

        # Cache instrument IDs
        async with get_db_session() as session:
            repo = InstrumentRepository(session)
            instruments = await repo.list_active()
            for inst in instruments:
                if inst.venue == "delta":
                    self.instrument_map[inst.canonical_symbol] = inst.id

        logger.info(f"Loaded {len(self.instrument_map)} active Delta instruments into memory.", map=self.instrument_map)

        # Bootstrap historical candles via REST if DB has few/no candles
        from swaram.providers.crypto.delta_rest import DeltaRestClient
        from swaram.core.time import from_epoch_us, to_utc
        from swaram.storage.repositories.market_repo import MarketDataRepository

        rest_client = DeltaRestClient(self.settings.delta_rest_url)
        async with get_db_session() as session:
            market_repo = MarketDataRepository(session)
            for canonical, inst_id in self.instrument_map.items():
                existing = await market_repo.get_recent_candles(inst_id, timeframe="1m", limit=10)
                if len(existing) < 10:
                    delta_symbol = canonical.split(":")[-1].replace("/", "")
                    logger.info(f"Bootstrapping historical candles for {canonical} ({delta_symbol}) via REST...")
                    raw_candles = await rest_client.get_candles(delta_symbol, resolution="1m", limit=100)
                    candles_to_seed = []
                    for c in raw_candles:
                        if isinstance(c, dict):
                            raw_t = c.get("time") or c.get("timestamp")
                            c_ts = from_epoch_us(raw_t) if raw_t else None
                            if c_ts:
                                candles_to_seed.append(Candle(
                                    timestamp=c_ts,
                                    instrument_id=inst_id,
                                    provider="delta",
                                    timeframe="1m",
                                    open=float(c.get("open", 0)),
                                    high=float(c.get("high", 0)),
                                    low=float(c.get("low", 0)),
                                    close=float(c.get("close", 0)),
                                    volume=float(c.get("volume", 0)),
                                    trade_count=int(c.get("trades", 0)),
                                ))
                    if candles_to_seed:
                        await market_repo.add_candles(candles_to_seed)
                        logger.info(f"Seeded {len(candles_to_seed)} historical candles for {canonical}.")

    async def _flush_loop(self) -> None:
        """Background task periodically flushing buffered market events to Postgres."""
        while self._running:
            try:
                await asyncio.sleep(self.settings.db_flush_interval_sec)
                await self._flush_buffers()
                # Update health in Redis
                await self.redis_store.update_provider_health("delta", self.provider.health.to_dict())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic DB flush", error=str(e))

    async def _flush_buffers(self) -> None:
        if not (self._ticks_buf or self._trades_buf or self._candles_buf or self._orderbook_buf or self._funding_buf):
            return

        async with get_db_session() as session:
            repo = MarketDataRepository(session)
            if self._ticks_buf:
                ticks_to_write = self._ticks_buf[:]
                self._ticks_buf.clear()
                await repo.add_ticks(ticks_to_write)

            if self._trades_buf:
                trades_to_write = self._trades_buf[:]
                self._trades_buf.clear()
                await repo.add_trades(trades_to_write)

            if self._candles_buf:
                candles_to_write = self._candles_buf[:]
                self._candles_buf.clear()
                await repo.add_candles(candles_to_write)

            if self._orderbook_buf:
                ob_to_write = self._orderbook_buf[:]
                self._orderbook_buf.clear()
                await repo.add_orderbook_snapshots(ob_to_write)

            if self._funding_buf:
                funding_to_write = self._funding_buf[:]
                self._funding_buf.clear()
                await repo.add_funding_rates(funding_to_write)

    async def start(self) -> None:
        self._running = True
        await self.initialize()
        await self.provider.connect()

        flush_task = asyncio.create_task(self._flush_loop())

        logger.info("Delta Collector started. Streaming real-time events...")
        try:
            async for event in self.provider.stream_events():
                if not self._running:
                    break
                await self._process_event(event)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            flush_task.cancel()
            await self._flush_buffers()
            await self.provider.disconnect()
            await close_redis()
            await close_db()
            logger.info("Delta Collector shut down cleanly.")

    async def _process_event(self, event: object) -> None:
        canonical = getattr(event, "canonical_symbol", "")
        inst_id = self.instrument_map.get(canonical)

        if isinstance(event, TickEvent):
            # Update Redis snapshot
            await self.redis_store.update_snapshot(canonical, {
                "canonical_symbol": canonical,
                "bid": event.bid,
                "ask": event.ask,
                "mid": event.mid,
                "last": event.last,
                "bid_size": event.bid_size,
                "ask_size": event.ask_size,
                "latency_ms": event.latency_ms,
                "timestamp": event.timestamp.isoformat(),
            })
            if inst_id:
                self._ticks_buf.append(Tick(
                    timestamp=event.timestamp,
                    instrument_id=inst_id,
                    provider="delta",
                    bid=event.bid,
                    ask=event.ask,
                    mid=event.mid,
                    last=event.last,
                    bid_size=event.bid_size,
                    ask_size=event.ask_size,
                    source_timestamp=event.source_timestamp,
                ))

        elif isinstance(event, TradeEvent):
            await self.redis_store.update_snapshot(canonical, {
                "last_price": event.price,
                "last_size": event.size,
                "last_side": event.side,
                "last_trade_at": event.timestamp.isoformat(),
            })
            if inst_id:
                self._trades_buf.append(Trade(
                    timestamp=event.timestamp,
                    instrument_id=inst_id,
                    provider="delta",
                    trade_id=event.trade_id or "",
                    price=event.price,
                    size=event.size,
                    side=event.side,
                ))

        elif isinstance(event, CandleEvent):
            await self.redis_store.update_snapshot(canonical, {
                f"candle_{event.timeframe}_close": event.close,
                f"candle_{event.timeframe}_volume": event.volume,
            })
            if inst_id:
                self._candles_buf.append(Candle(
                    timestamp=event.timestamp,
                    instrument_id=inst_id,
                    provider="delta",
                    timeframe=event.timeframe,
                    open=event.open,
                    high=event.high,
                    low=event.low,
                    close=event.close,
                    volume=event.volume,
                    trade_count=event.trade_count,
                ))

        elif isinstance(event, OrderbookEvent):
            await self.redis_store.update_snapshot(canonical, {
                "best_bid": event.best_bid,
                "best_ask": event.best_ask,
                "spread": event.spread,
                "spread_bps": event.spread_bps,
                "book_imbalance": event.imbalance,
                "microprice": event.microprice,
                "bid_depth": event.bid_depth,
                "ask_depth": event.ask_depth,
            })
            if inst_id:
                self._orderbook_buf.append(OrderbookSnapshot(
                    timestamp=event.timestamp,
                    instrument_id=inst_id,
                    provider="delta",
                    depth=event.depth,
                    best_bid=event.best_bid,
                    best_ask=event.best_ask,
                    spread=event.spread,
                    bid_depth=event.bid_depth,
                    ask_depth=event.ask_depth,
                    imbalance=event.imbalance,
                    microprice=event.microprice,
                ))

        elif isinstance(event, FundingEvent):
            await self.redis_store.update_snapshot(canonical, {
                "funding_rate": event.funding_rate,
                "next_funding_time": event.next_funding_time.isoformat() if event.next_funding_time else None,
            })
            if inst_id:
                self._funding_buf.append(FundingRate(
                    timestamp=event.timestamp,
                    instrument_id=inst_id,
                    provider="delta",
                    funding_rate=event.funding_rate,
                    next_funding_time=event.next_funding_time,
                ))

        elif isinstance(event, MarkSpotPriceEvent):
            updates = {}
            if event.mark_price is not None:
                updates["mark_price"] = event.mark_price
            if event.spot_price is not None:
                updates["spot_price"] = event.spot_price
            if updates:
                await self.redis_store.update_snapshot(canonical, updates)

        # Trigger batch flush if buffer size exceeded
        if (
            len(self._ticks_buf) >= self.settings.db_batch_size
            or len(self._trades_buf) >= self.settings.db_batch_size
            or len(self._candles_buf) >= self.settings.db_batch_size
        ):
            await self._flush_buffers()


async def main():
    setup_logging()
    runner = DeltaCollectorRunner()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(runner.provider.disconnect()))
        except NotImplementedError:
            pass  # Windows event loop support

    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
