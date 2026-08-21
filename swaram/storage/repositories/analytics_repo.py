from datetime import datetime
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.models.analytics import IndicatorSnapshot, MarketStructureEvent


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_structure_events(self, events: List[MarketStructureEvent]) -> None:
        if events:
            self.session.add_all(events)

    async def add_indicator_snapshot(self, snapshot: IndicatorSnapshot) -> None:
        self.session.add(snapshot)

    async def get_recent_structure_events(
        self,
        instrument_id: int,
        timeframe: str = "1m",
        limit: int = 50,
    ) -> List[MarketStructureEvent]:
        stmt = (
            select(MarketStructureEvent)
            .where(
                MarketStructureEvent.instrument_id == instrument_id,
                MarketStructureEvent.timeframe == timeframe,
            )
            .order_by(desc(MarketStructureEvent.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_fvgs(
        self,
        instrument_id: int,
        timeframe: str = "1m",
    ) -> List[MarketStructureEvent]:
        stmt = (
            select(MarketStructureEvent)
            .where(
                MarketStructureEvent.instrument_id == instrument_id,
                MarketStructureEvent.timeframe == timeframe,
                MarketStructureEvent.event_type == "FVG",
                MarketStructureEvent.is_mitigated == False,
            )
            .order_by(desc(MarketStructureEvent.timestamp))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_indicator_snapshot(
        self,
        instrument_id: int,
        timeframe: str = "1m",
    ) -> Optional[IndicatorSnapshot]:
        stmt = (
            select(IndicatorSnapshot)
            .where(
                IndicatorSnapshot.instrument_id == instrument_id,
                IndicatorSnapshot.timeframe == timeframe,
            )
            .order_by(desc(IndicatorSnapshot.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
