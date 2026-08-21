from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.models.instrument import Instrument


class InstrumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_canonical(self, canonical_symbol: str) -> Optional[Instrument]:
        stmt = select(Instrument).where(Instrument.canonical_symbol == canonical_symbol.upper())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_venue_symbol(self, venue: str, provider_symbol: str) -> Optional[Instrument]:
        stmt = select(Instrument).where(
            Instrument.venue == venue.lower(),
            Instrument.provider_symbol == provider_symbol.upper(),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_create(
        self,
        canonical_symbol: str,
        asset_class: str,
        base_asset: str,
        quote_asset: str,
        venue: str,
        provider_symbol: str,
        tick_size: Optional[float] = None,
        lot_size: Optional[float] = None,
    ) -> Instrument:
        inst = await self.get_by_venue_symbol(venue, provider_symbol)
        if inst is not None:
            return inst

        inst = Instrument(
            canonical_symbol=canonical_symbol.upper(),
            asset_class=asset_class.lower(),
            base_asset=base_asset.upper(),
            quote_asset=quote_asset.upper(),
            venue=venue.lower(),
            provider_symbol=provider_symbol.upper(),
            tick_size=tick_size,
            lot_size=lot_size,
            active=True,
        )
        self.session.add(inst)
        await self.session.flush()
        return inst

    async def list_active(self) -> List[Instrument]:
        stmt = select(Instrument).where(Instrument.active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
