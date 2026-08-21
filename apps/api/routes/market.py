from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_redis_store, get_session
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc
from swaram.storage.redis import RedisLiveStore
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/{symbol}", summary="Get Live Market Snapshot for Symbol")
async def get_market_snapshot(
    symbol: str,
    session: AsyncSession = Depends(get_session),
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    
    # 1. Fetch live snapshot from Redis
    snapshot = await redis_store.get_snapshot(canonical)

    # 2. Check provider health
    health = await redis_store.get_provider_health("delta")

    if snapshot:
        return {
            "canonical_symbol": canonical,
            "requested_symbol": symbol,
            "source": "redis_live_snapshot",
            "snapshot": snapshot,
            "provider_health": health,
        }

    # 3. Fallback to database if redis is warming up
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(
            status_code=404,
            detail=f"Instrument '{symbol}' (canonical '{canonical}') not found in universe.",
        )

    market_repo = MarketDataRepository(session)
    latest_tick = await market_repo.get_latest_tick(inst.id)
    latest_ob = await market_repo.get_latest_orderbook(inst.id)

    if not latest_tick and not latest_ob:
        # Fallback to REST endpoint snapshot
        if inst.venue == "delta":
            from swaram.providers.crypto.delta_rest import DeltaRestClient
            from swaram.config.settings import get_settings
            rest_client = DeltaRestClient(get_settings().delta_rest_url)
            ticker_data = await rest_client.get_ticker(inst.provider_symbol)
            if ticker_data:
                quotes = ticker_data.get("quotes") or {}
                last = float(ticker_data.get("close") or ticker_data.get("last_price") or 0.0) or None
                bid = float(quotes.get("best_bid") or ticker_data.get("best_bid") or 0.0) or None
                ask = float(quotes.get("best_ask") or ticker_data.get("best_ask") or 0.0) or None
                spread = round(ask - bid, 4) if ask and bid else None
                rest_snap = {
                    "canonical_symbol": canonical,
                    "bid": bid,
                    "ask": ask,
                    "mid": round((bid + ask) / 2.0, 4) if bid and ask else last,
                    "last": last,
                    "spread": spread,
                    "timestamp": iso_utc(),
                }
                await redis_store.update_snapshot(canonical, rest_snap)
                return {
                    "canonical_symbol": canonical,
                    "requested_symbol": symbol,
                    "source": "delta_rest_fallback",
                    "snapshot": rest_snap,
                    "provider_health": health,
                }
        elif inst.venue == "ctrader":
            from swaram.providers.forex.ctrader import _fetch_all_prices, SPREADS
            prices = await _fetch_all_prices([inst.provider_symbol])
            mid = prices.get(inst.provider_symbol)
            if mid:
                spread = SPREADS.get(inst.provider_symbol, 0.0001)
                bid = round(mid - spread / 2.0, 5)
                ask = round(mid + spread / 2.0, 5)
                rest_snap = {
                    "canonical_symbol": canonical,
                    "bid": bid,
                    "ask": ask,
                    "mid": mid,
                    "last": mid,
                    "spread": spread,
                    "timestamp": iso_utc(),
                }
                await redis_store.update_snapshot(canonical, rest_snap)
                return {
                    "canonical_symbol": canonical,
                    "requested_symbol": symbol,
                    "source": "yahoo_rest_fallback",
                    "snapshot": rest_snap,
                    "provider_health": health,
                }

        return {
            "canonical_symbol": canonical,
            "requested_symbol": symbol,
            "source": "database_empty",
            "message": "No tick data recorded yet for this instrument.",
            "provider_health": health,
        }

    return {
        "canonical_symbol": canonical,
        "requested_symbol": symbol,
        "source": "database_fallback",
        "snapshot": {
            "bid": latest_tick.bid if latest_tick else None,
            "ask": latest_tick.ask if latest_tick else None,
            "mid": latest_tick.mid if latest_tick else None,
            "last": latest_tick.last if latest_tick else None,
            "best_bid": latest_ob.best_bid if latest_ob else None,
            "best_ask": latest_ob.best_ask if latest_ob else None,
            "spread": latest_ob.spread if latest_ob else None,
            "book_imbalance": latest_ob.imbalance if latest_ob else None,
            "microprice": latest_ob.microprice if latest_ob else None,
        },
        "provider_health": health,
    }


@router.get("/{symbol}/candles", summary="Get Historical OHLCV Candles")
async def get_candles(
    symbol: str,
    timeframe: str = Query("1m", pattern="^(1m|5m|15m|1h|4h|1d)$"),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=limit)

    return {
        "canonical_symbol": canonical,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": [
            {
                "timestamp": iso_utc(c.timestamp),
                "timestamp_ist": iso_ist(c.timestamp),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "trade_count": c.trade_count,
            }
            for c in candles
        ],
    }


@router.get("/{symbol}/orderbook", summary="Get Orderbook Depth Metrics")
async def get_orderbook(
    symbol: str,
    session: AsyncSession = Depends(get_session),
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    snapshot = await redis_store.get_snapshot(canonical)

    if snapshot and "best_bid" in snapshot:
        return {
            "canonical_symbol": canonical,
            "source": "redis_live",
            "best_bid": snapshot.get("best_bid"),
            "best_ask": snapshot.get("best_ask"),
            "spread": snapshot.get("spread"),
            "spread_bps": snapshot.get("spread_bps"),
            "book_imbalance": snapshot.get("book_imbalance"),
            "microprice": snapshot.get("microprice"),
            "bid_depth": snapshot.get("bid_depth"),
            "ask_depth": snapshot.get("ask_depth"),
        }

    # Fallback to DB
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    ob = await market_repo.get_latest_orderbook(inst.id)
    if not ob:
        raise HTTPException(status_code=404, detail="No orderbook snapshot available yet.")

    return {
        "canonical_symbol": canonical,
        "source": "database",
        "timestamp": iso_utc(ob.timestamp),
        "timestamp_ist": iso_ist(ob.timestamp),
        "best_bid": ob.best_bid,
        "best_ask": ob.best_ask,
        "spread": ob.spread,
        "book_imbalance": ob.imbalance,
        "microprice": ob.microprice,
        "bid_depth": ob.bid_depth,
        "ask_depth": ob.ask_depth,
    }
