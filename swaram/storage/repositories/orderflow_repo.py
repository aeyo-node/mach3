from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.models.orderflow import OrderflowAnalyticsSnapshot, PositioningRecord


class OrderflowRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_orderflow_snapshot(self, snapshot: OrderflowAnalyticsSnapshot) -> None:
        self.session.add(snapshot)

    async def add_positioning_record(self, record: PositioningRecord) -> None:
        self.session.add(record)

    async def get_latest_orderflow_snapshot(self, instrument_id: int) -> Optional[OrderflowAnalyticsSnapshot]:
        stmt = (
            select(OrderflowAnalyticsSnapshot)
            .where(OrderflowAnalyticsSnapshot.instrument_id == instrument_id)
            .order_by(desc(OrderflowAnalyticsSnapshot.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_latest_positioning_record(self, instrument_id: int) -> Optional[PositioningRecord]:
        stmt = (
            select(PositioningRecord)
            .where(PositioningRecord.instrument_id == instrument_id)
            .order_by(desc(PositioningRecord.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
