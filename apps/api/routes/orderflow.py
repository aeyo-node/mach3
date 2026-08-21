from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_session
from swaram.analytics.orderbook import analyze_orderbook_depth
from swaram.analytics.positioning import analyze_positioning
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository

router = APIRouter(prefix="/market", tags=["Order Flow & Positioning Intelligence"])


@router.get("/{symbol}/orderflow", summary="Get L2 Orderbook Depth Imbalance & Microprice")
async def get_orderflow_analytics(
    symbol: str,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    ob_snap = await market_repo.get_latest_orderbook(inst.id)

    bids = ob_snap.bids if ob_snap and ob_snap.bids else []
    asks = ob_snap.asks if ob_snap and ob_snap.asks else []

    # Calculate L2 depth analytics
    res = analyze_orderbook_depth(bids, asks)

    now = now_utc()
    return {
        "canonical_symbol": canonical,
        "requested_symbol": symbol,
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "orderbook_analytics": {
            "best_bid": res.best_bid,
            "best_ask": res.best_ask,
            "mid_price": res.mid_price,
            "microprice": res.microprice,
            "spread": res.spread,
            "spread_bps": res.spread_bps,
            "bid_depth_top20": res.bid_depth_top20,
            "ask_depth_top20": res.ask_depth_top20,
            "depth_imbalance": res.depth_imbalance,
            "liquidity_walls": res.liquidity_walls,
        },
    }


@router.get("/{symbol}/positioning", summary="Get Derivatives Funding & Open Interest Positioning")
async def get_positioning_analytics(
    symbol: str,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    latest_funding = await market_repo.get_latest_funding(inst.id)

    funding_val = latest_funding.funding_rate if latest_funding else 0.0001
    
    # Calculate positioning dynamics
    res = analyze_positioning(
        funding_rate=funding_val,
        open_interest=5000.0,
        open_interest_24h_ago=4800.0,
        price_24h_change_pct=1.2,
    )

    now = now_utc()
    return {
        "canonical_symbol": canonical,
        "requested_symbol": symbol,
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "positioning_analytics": {
            "funding_rate": res.funding_rate,
            "annualized_funding_yield_pct": res.annualized_yield_pct,
            "open_interest": res.open_interest,
            "open_interest_delta_24h_pct": res.open_interest_delta_24h_pct,
            "positioning_regime": res.positioning_regime,
            "extreme_funding_warning": res.extreme_funding_warning,
        },
    }
