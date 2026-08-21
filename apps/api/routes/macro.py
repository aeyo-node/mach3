from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_session
from swaram.analytics.macro_watchdog import MacroEventWatchdog
from swaram.core.time import iso_ist, iso_utc
from swaram.providers.macro.calendar import EconomicCalendarProvider
from swaram.storage.repositories.instrument_repo import InstrumentRepository

router = APIRouter(tags=["Macroeconomic Intelligence & Market Universe"])


@router.get("/macro/events", summary="Get Economic Calendar Events")
async def get_macro_events() -> Dict[str, Any]:
    provider = EconomicCalendarProvider()
    events = await provider.get_upcoming_events(days_ahead=7)
    return {
        "timestamp_utc": iso_utc(),
        "timestamp_ist": iso_ist(),
        "total_events": len(events),
        "events": events,
    }


@router.get("/macro/watchdog", summary="Evaluate Macro Risk Window")
async def get_macro_watchdog() -> Dict[str, Any]:
    provider = EconomicCalendarProvider()
    events = await provider.get_upcoming_events(days_ahead=7)
    watchdog = MacroEventWatchdog(buffer_minutes=15)
    return watchdog.evaluate_risk_window(events)


@router.get("/market/universe", summary="Get Multi-Asset Universe Breakdown")
async def get_market_universe(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    repo = InstrumentRepository(session)
    instruments = await repo.list_active()

    by_asset_class: Dict[str, List[Dict[str, Any]]] = {}
    for inst in instruments:
        ac = inst.asset_class.upper()
        if ac not in by_asset_class:
            by_asset_class[ac] = []
        by_asset_class[ac].append({
            "canonical_symbol": inst.canonical_symbol,
            "base_asset": inst.base_asset,
            "quote_asset": inst.quote_asset,
            "venue": inst.venue,
            "provider_symbol": inst.provider_symbol,
            "tick_size": inst.tick_size,
            "lot_size": inst.lot_size,
        })

    return {
        "timestamp_utc": iso_utc(),
        "timestamp_ist": iso_ist(),
        "total_instruments": len(instruments),
        "asset_classes": by_asset_class,
    }
