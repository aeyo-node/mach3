from datetime import datetime
from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.models.macro import MacroEvent


class MacroRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_macro_events(self, events: List[MacroEvent]) -> None:
        if events:
            self.session.add_all(events)

    async def get_upcoming_events(self, limit: int = 20) -> List[MacroEvent]:
        stmt = (
            select(MacroEvent)
            .order_by(desc(MacroEvent.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
