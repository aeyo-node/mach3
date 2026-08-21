import asyncio
import signal
from typing import Dict, List
from swaram.config.settings import get_settings
from swaram.core.events import TickEvent
from swaram.core.logging import get_logger, setup_logging
from swaram.models.market_data import Tick
from swaram.providers.forex.ctrader import CTraderForexProvider
from swaram.storage.postgres import close_db, get_db_session, init_db
from swaram.storage.redis import RedisLiveStore, close_redis, get_redis
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository
from swaram.storage.seed import seed_instruments

logger = get_logger("collector.multi_asset")


class MultiAssetRunner:
    def __init__(self):
        self.settings = get_settings()
        self.provider = CTraderForexProvider()
        self.redis_store = RedisLiveStore(get_redis())
        self.instrument_map: Dict[str, int] = {}
        self._running = False
        self._ticks_buf: List[Tick] = []

    async def initialize(self) -> None:
        logger.info("Initializing Multi-Asset Forex/Metals Runner...")
        await init_db()
        await seed_instruments()

        async with get_db_session() as session:
            repo = InstrumentRepository(session)
            instruments = await repo.list_active()
            for inst in instruments:
                if inst.venue == "ctrader":
                    self.instrument_map[inst.canonical_symbol] = inst.id

        logger.info(f"Loaded {len(self.instrument_map)} active Forex/Metals instruments into memory.")

    async def _flush_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self.settings.db_flush_interval_sec)
                await self._flush_buffers()
                await self.redis_store.update_provider_health("ctrader", self.provider.health.to_dict())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in multi-asset DB flush", error=str(e))

    async def _flush_buffers(self) -> None:
        if not self._ticks_buf:
            return
        async with get_db_session() as session:
            repo = MarketDataRepository(session)
            ticks_to_write = self._ticks_buf[:]
            self._ticks_buf.clear()
            await repo.add_ticks(ticks_to_write)

    async def start(self) -> None:
        self._running = True
        await self.initialize()
        await self.provider.connect()

        flush_task = asyncio.create_task(self._flush_loop())

        logger.info("Multi-Asset Collector started. Streaming Forex & Metals events...")
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
            logger.info("Multi-Asset Collector shut down cleanly.")

    async def _process_event(self, event: object) -> None:
        canonical = getattr(event, "canonical_symbol", "")
        inst_id = self.instrument_map.get(canonical)

        if isinstance(event, TickEvent):
            await self.redis_store.update_snapshot(canonical, {
                "canonical_symbol": canonical,
                "bid": event.bid,
                "ask": event.ask,
                "mid": event.mid,
                "last": event.last,
                "spread": round(event.ask - event.bid, 5) if event.ask and event.bid else None,
                "timestamp": event.timestamp.isoformat(),
            })
            if inst_id:
                self._ticks_buf.append(Tick(
                    timestamp=event.timestamp,
                    instrument_id=inst_id,
                    provider="ctrader",
                    bid=event.bid,
                    ask=event.ask,
                    mid=event.mid,
                    last=event.last,
                    bid_size=event.bid_size,
                    ask_size=event.ask_size,
                    source_timestamp=event.source_timestamp,
                ))

        if len(self._ticks_buf) >= self.settings.db_batch_size:
            await self._flush_buffers()


async def main():
    setup_logging()
    runner = MultiAssetRunner()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(runner.provider.disconnect()))
        except NotImplementedError:
            pass

    await runner.start()


if __name__ == "__main__":
    asyncio.run(main())
