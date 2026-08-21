from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_redis_store, get_session
from swaram.analytics.engine import compute_analytics
from swaram.core.events import CandleEvent
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc, to_utc
from swaram.storage.redis import RedisLiveStore
from swaram.storage.repositories.analytics_repo import AnalyticsRepository
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository

router = APIRouter(prefix="/market", tags=["Analytics & Market Structure"])


@router.get("/{symbol}/indicators", summary="Get Live Technical Indicators")
async def get_indicators(
    symbol: str,
    timeframe: str = Query("1m", pattern="^(1m|5m|15m|1h|4h|1d)$"),
    session: AsyncSession = Depends(get_session),
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)

    if not db_candles:
        return {
            "canonical_symbol": canonical,
            "requested_symbol": symbol,
            "timeframe": timeframe,
            "message": "Insufficient historical candles to calculate indicators.",
            "indicators": {},
        }

    # Convert DB candles to CandleEvents
    events = [
        CandleEvent(
            canonical_symbol=canonical,
            provider=c.provider,
            timeframe=c.timeframe,
            timestamp=c.timestamp,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
            trade_count=c.trade_count,
        )
        for c in db_candles
    ]

    snapshot = compute_analytics(canonical, timeframe, events)
    return snapshot.to_dict()


@router.get("/{symbol}/structure", summary="Get Technical Market Structure (BOS, CHoCH, FVG, Order Blocks)")
async def get_market_structure(
    symbol: str,
    timeframe: str = Query("1m", pattern="^(1m|5m|15m|1h|4h|1d)$"),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)

    if not db_candles:
        return {
            "canonical_symbol": canonical,
            "requested_symbol": symbol,
            "timeframe": timeframe,
            "message": "Insufficient historical candles for market structure analysis.",
            "market_structure": {},
        }

    events = [
        CandleEvent(
            canonical_symbol=canonical,
            provider=c.provider,
            timeframe=c.timeframe,
            timestamp=c.timestamp,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
            trade_count=c.trade_count,
        )
        for c in db_candles
    ]

    snapshot = compute_analytics(canonical, timeframe, events)
    res_dict = snapshot.to_dict()

    return {
        "canonical_symbol": canonical,
        "timeframe": timeframe,
        "timestamp_utc": res_dict["timestamp_utc"],
        "timestamp_ist": res_dict["timestamp_ist"],
        "volume_profile": res_dict["volume_profile"],
        "market_structure": res_dict["market_structure"],
    }
