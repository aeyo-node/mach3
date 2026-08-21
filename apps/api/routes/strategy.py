from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from apps.api.deps import get_redis_store
from swaram.agents.loop import (
    StrategyRunner,
    get_runner,
    set_runner,
    remove_runner,
)
from swaram.agents.strategy import STRATEGY_REGISTRY
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.storage.redis import RedisLiveStore

router = APIRouter(prefix="/strategy", tags=["AI Agent Strategy Loop"])


class StrategyStartRequest(BaseModel):
    symbol: str
    strategy: str = "momentum"
    interval_sec: float = 10.0
    capital: float = 10000.0


@router.post("/run", summary="Execute One Strategy Cycle (Single Shot)")
async def strategy_run_once(
    request: StrategyStartRequest,
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    strat = STRATEGY_REGISTRY.get(request.strategy)
    if not strat:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{request.strategy}'. Available: {list(STRATEGY_REGISTRY.keys())}",
        )

    runner = StrategyRunner(
        symbol=request.symbol,
        strategy=strat,
        redis_store=redis_store,
        interval_sec=request.interval_sec,
        capital=request.capital,
    )
    result = await runner.run_once()
    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        **result,
    }


@router.post("/start", summary="Start Autonomous Strategy Loop")
async def strategy_start(
    request: StrategyStartRequest,
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    if get_runner(request.symbol) is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Strategy loop already running for '{request.symbol}'. Stop it first.",
        )

    strat = STRATEGY_REGISTRY.get(request.strategy)
    if not strat:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{request.strategy}'. Available: {list(STRATEGY_REGISTRY.keys())}",
        )

    runner = StrategyRunner(
        symbol=request.symbol,
        strategy=strat,
        redis_store=redis_store,
        interval_sec=request.interval_sec,
        capital=request.capital,
    )
    set_runner(request.symbol, runner)
    runner.start()

    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "status": "started",
        "symbol": request.symbol,
        "strategy": request.strategy,
        "interval_sec": request.interval_sec,
    }


@router.post("/stop/{symbol}", summary="Stop Autonomous Strategy Loop")
async def strategy_stop(symbol: str) -> Dict[str, Any]:
    runner = get_runner(symbol)
    if not runner:
        raise HTTPException(status_code=404, detail=f"No active strategy loop for '{symbol}'.")

    runner.stop()
    remove_runner(symbol)
    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "status": "stopped",
        "symbol": symbol,
    }


@router.get("/status/{symbol}", summary="Get Strategy Loop Status")
async def strategy_status(symbol: str) -> Dict[str, Any]:
    runner = get_runner(symbol)
    if not runner:
        return {
            "symbol": symbol,
            "running": False,
            "message": "No active strategy loop.",
        }
    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        **runner.status(),
    }


@router.get("/list", summary="List Available Strategies")
async def list_strategies() -> Dict[str, Any]:
    return {
        "strategies": list(STRATEGY_REGISTRY.keys()),
        "descriptions": {
            "momentum": "RSI < 35 + price above VWAP → buy; RSI > 65 → sell",
            "mean_reversion": "Price touches lower Bollinger Band → buy; recovers to midline → sell",
        },
    }
