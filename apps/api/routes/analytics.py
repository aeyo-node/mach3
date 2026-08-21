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


async def _get_or_fetch_candles(session: AsyncSession, inst: Any, canonical: str, timeframe: str) -> List[CandleEvent]:
    market_repo = MarketDataRepository(session)
    db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)

    if len(db_candles) < 10:
        from swaram.providers.crypto.delta_rest import DeltaRestClient
        from swaram.config.settings import get_settings
        from swaram.core.time import from_epoch_us
        from swaram.models.market_data import Candle

        settings = get_settings()
        rest_client = DeltaRestClient(settings.delta_rest_url)
        delta_symbol = inst.provider_symbol
        raw_candles = await rest_client.get_candles(delta_symbol, resolution=timeframe, limit=100)
        
        candles_to_seed = []
        for c in raw_candles:
            if isinstance(c, dict):
                raw_t = c.get("time") or c.get("timestamp")
                c_ts = from_epoch_us(raw_t) if raw_t else None
                if c_ts:
                    candles_to_seed.append(Candle(
                        timestamp=c_ts,
                        instrument_id=inst.id,
                        provider="delta",
                        timeframe=timeframe,
                        open=float(c.get("open", 0)),
                        high=float(c.get("high", 0)),
                        low=float(c.get("low", 0)),
                        close=float(c.get("close", 0)),
                        volume=float(c.get("volume", 0)),
                        trade_count=int(c.get("trades", 0)),
                    ))
        if candles_to_seed:
            await market_repo.add_candles(candles_to_seed)
            await session.commit()
            db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)

    return [
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

    events = await _get_or_fetch_candles(session, inst, canonical, timeframe)
    if not events:
        return {
            "canonical_symbol": canonical,
            "requested_symbol": symbol,
            "timeframe": timeframe,
            "message": "Insufficient historical candles to calculate indicators.",
            "indicators": {},
        }

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

    events = await _get_or_fetch_candles(session, inst, canonical, timeframe)
    if not events:
        return {
            "canonical_symbol": canonical,
            "requested_symbol": symbol,
            "timeframe": timeframe,
            "message": "Insufficient historical candles for market structure analysis.",
            "market_structure": {},
        }

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
