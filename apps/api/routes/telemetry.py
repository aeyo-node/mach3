from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_redis_store, get_session
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.models.anomaly import MarketAnomalyRecord
from swaram.storage.redis import RedisLiveStore
from swaram.storage.repositories.instrument_repo import InstrumentRepository

router = APIRouter(tags=["Production Telemetry & Anomaly Analytics"])


@router.get("/health/telemetry", summary="Get Swaram Market Engine Ingestion Telemetry")
async def get_health_telemetry(
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    # Fetch provider health from Redis
    delta_health = await redis_store.get_provider_health("delta") or {}
    ctrader_health = await redis_store.get_provider_health("ctrader") or {}

    now = now_utc()
    return {
        "status": "operational",
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "collectors": {
            "delta": {
                "active": delta_health.get("connected", False),
                "last_message_at": delta_health.get("last_message_at"),
                "total_messages": delta_health.get("message_count", 0),
                "reconnect_count": delta_health.get("reconnect_count", 0),
                "errors": delta_health.get("error_count", 0),
            },
            "ctrader": {
                "active": ctrader_health.get("connected", False),
                "last_message_at": ctrader_health.get("last_message_at"),
                "total_messages": ctrader_health.get("message_count", 0),
                "reconnect_count": ctrader_health.get("reconnect_count", 0),
                "errors": ctrader_health.get("error_count", 0),
            },
        },
        "redis_store": {
            "status": "connected",
        },
    }


@router.get("/market/anomalies", summary="Get Live Feed of Market Anomalies")
async def get_market_anomalies(
    symbol: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    inst_id = None
    if symbol:
        canonical = resolve_canonical(symbol)
        inst_repo = InstrumentRepository(session)
        inst = await inst_repo.get_by_canonical(canonical)
        if not inst:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in universe.")
        inst_id = inst.id

    stmt = select(MarketAnomalyRecord).order_by(desc(MarketAnomalyRecord.timestamp)).limit(limit)
    if inst_id:
        stmt = stmt.where(MarketAnomalyRecord.instrument_id == inst_id)

    result = await session.execute(stmt)
    records = result.scalars().all()

    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "total_anomalies": len(records),
        "anomalies": [
            {
                "id": r.id,
                "timestamp": iso_utc(r.timestamp),
                "provider": r.provider,
                "anomaly_type": r.anomaly_type,
                "severity": r.severity,
                "description": r.description,
                "trigger_value": r.trigger_value,
                "threshold_value": r.threshold_value,
            }
            for r in records
        ],
    }
