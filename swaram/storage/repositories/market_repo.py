from datetime import datetime
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.models.market_data import (
    Candle,
    FundingRate,
    OpenInterest,
    OrderbookSnapshot,
    Tick,
    Trade,
)


class MarketDataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_ticks(self, ticks: List[Tick]) -> None:
        if ticks:
            self.session.add_all(ticks)

    async def add_trades(self, trades: List[Trade]) -> None:
        if trades:
            self.session.add_all(trades)

    async def add_candles(self, candles: List[Candle]) -> None:
        if candles:
            self.session.add_all(candles)

    async def add_orderbook_snapshots(self, snapshots: List[OrderbookSnapshot]) -> None:
        if snapshots:
            self.session.add_all(snapshots)

    async def add_funding_rates(self, fundings: List[FundingRate]) -> None:
        if fundings:
            self.session.add_all(fundings)

    async def get_recent_candles(
        self,
        instrument_id: int,
        timeframe: str = "1m",
        limit: int = 100,
    ) -> List[Candle]:
        stmt = (
            select(Candle)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == timeframe,
            )
            .order_by(desc(Candle.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        candles = list(result.scalars().all())
        # Return in ascending chronological order
        return sorted(candles, key=lambda c: c.timestamp)

    async def get_latest_tick(self, instrument_id: int) -> Optional[Tick]:
        stmt = (
            select(Tick)
            .where(Tick.instrument_id == instrument_id)
            .order_by(desc(Tick.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_latest_orderbook(self, instrument_id: int) -> Optional[OrderbookSnapshot]:
        stmt = (
            select(OrderbookSnapshot)
            .where(OrderbookSnapshot.instrument_id == instrument_id)
            .order_by(desc(OrderbookSnapshot.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
