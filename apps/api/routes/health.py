from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_redis_store, get_session
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.storage.redis import RedisLiveStore

router = APIRouter(prefix="/health", tags=["Health"])

START_TIME = now_utc()


@router.get("", summary="Overall System Health Check")
async def health_check(
    session: AsyncSession = Depends(get_session),
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    # Check Database
    db_ok = False
    try:
        res = await session.execute(text("SELECT 1"))
        db_ok = res.scalar() == 1
    except Exception as e:
        db_err = str(e)

    # Check Redis
    redis_ok = False
    try:
        pong = await redis_store.client.ping()
        redis_ok = bool(pong)
    except Exception:
        pass

    uptime_seconds = (now_utc() - START_TIME).total_seconds()
    is_healthy = db_ok and redis_ok

    payload = {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp_utc": iso_utc(),
        "timestamp_ist": iso_ist(),
        "uptime_seconds": round(uptime_seconds, 2),
        "components": {
            "database": "connected" if db_ok else "unreachable",
            "redis": "connected" if redis_ok else "unreachable",
        },
    }

    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/providers", summary="Market Data Provider Status & Latencies")
async def providers_health(
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    providers = await redis_store.get_all_provider_health()
    all_healthy = True
    for p in providers:
        if p.get("status") in ("DISCONNECTED", "STALE"):
            all_healthy = False

    return {
        "timestamp_utc": iso_utc(),
        "timestamp_ist": iso_ist(),
        "all_providers_healthy": all_healthy,
        "providers": providers,
    }
