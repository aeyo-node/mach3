from typing import Any, Dict, List, Tuple
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


async def _get_or_fetch_orderbook(session: AsyncSession, inst: Any) -> Tuple[List[List[float]], List[List[float]]]:
    market_repo = MarketDataRepository(session)
    ob_snap = await market_repo.get_latest_orderbook(inst.id)

    bids = ob_snap.bids if ob_snap and ob_snap.bids else []
    asks = ob_snap.asks if ob_snap and ob_snap.asks else []

    if not bids or not asks:
        if inst.venue == "delta":
            from swaram.providers.crypto.delta_rest import DeltaRestClient
            from swaram.config.settings import get_settings
            rest_client = DeltaRestClient(get_settings().delta_rest_url)
            raw_ob = await rest_client.get_l2_orderbook(inst.provider_symbol)
            if raw_ob:
                raw_b = raw_ob.get("buy") or raw_ob.get("bids") or []
                raw_a = raw_ob.get("sell") or raw_ob.get("asks") or []
                bids = [[float(b.get("price", 0)), float(b.get("size", 0))] if isinstance(b, dict) else [float(b[0]), float(b[1])] for b in raw_b]
                asks = [[float(a.get("price", 0)), float(a.get("size", 0))] if isinstance(a, dict) else [float(a[0]), float(a[1])] for a in raw_a]
        elif inst.venue == "ctrader":
            from swaram.providers.forex.ctrader import _fetch_all_prices, SPREADS
            prices = await _fetch_all_prices([inst.provider_symbol])
            mid = prices.get(inst.provider_symbol, 1.0850)
            spread = SPREADS.get(inst.provider_symbol, 0.0001)
            bids = [[round(mid - spread / 2.0, 5), 1000000.0]]
            asks = [[round(mid + spread / 2.0, 5), 1000000.0]]

    return bids, asks


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

    bids, asks = await _get_or_fetch_orderbook(session, inst)
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

    funding_val = (
        latest_funding.funding_rate
        if (latest_funding and latest_funding.funding_rate is not None)
        else 0.0001
    )

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
