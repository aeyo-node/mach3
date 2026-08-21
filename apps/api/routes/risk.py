from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from apps.api.deps import get_redis_store
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.risk.engine import RiskEngine, RiskState
from swaram.storage.redis import RedisLiveStore

router = APIRouter(prefix="/risk", tags=["Risk Management Engine"])

_engine = RiskEngine()

# Default portfolio config — can be overridden via env in production
DEFAULT_INITIAL_CAPITAL = 10000.0
DEFAULT_MAX_DRAWDOWN_PCT = 10.0
DEFAULT_MAX_POSITION_PCT = 20.0
DEFAULT_MAX_LOSS_PER_TRADE_PCT = 2.0


class RiskCheckRequest(BaseModel):
    symbol: str
    requested_quantity: float
    current_capital: float = DEFAULT_INITIAL_CAPITAL
    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    position_size: float = 0.0
    entry_price: float = 0.0
    max_drawdown_pct: float = DEFAULT_MAX_DRAWDOWN_PCT
    max_position_pct: float = DEFAULT_MAX_POSITION_PCT
    max_loss_per_trade_pct: float = DEFAULT_MAX_LOSS_PER_TRADE_PCT


class PositionSizeRequest(BaseModel):
    method: str = "fixed_fractional"   # "kelly" or "fixed_fractional"
    capital: float = DEFAULT_INITIAL_CAPITAL
    current_price: float
    risk_pct: float = 2.0
    win_rate: float = 0.55
    avg_win: float = 100.0
    avg_loss: float = 50.0


@router.get("/state", summary="Get Current Portfolio Risk Exposure")
async def get_risk_state(
    capital: float = DEFAULT_INITIAL_CAPITAL,
    initial_capital: float = DEFAULT_INITIAL_CAPITAL,
    position_size: float = 0.0,
    current_price: float = 0.0,
) -> Dict[str, Any]:
    state = RiskState(
        current_capital=capital,
        initial_capital=initial_capital,
        position_size=position_size,
        entry_price=current_price,
        current_price=current_price,
        max_drawdown_pct=DEFAULT_MAX_DRAWDOWN_PCT,
        max_position_pct=DEFAULT_MAX_POSITION_PCT,
        max_loss_per_trade_pct=DEFAULT_MAX_LOSS_PER_TRADE_PCT,
    )

    drawdown_pct = _engine._drawdown_pct(state)
    exposure_pct = (position_size * current_price / initial_capital * 100.0) if initial_capital > 0 and current_price > 0 else 0.0

    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "current_capital": capital,
        "initial_capital": initial_capital,
        "drawdown_pct": round(drawdown_pct, 2),
        "exposure_pct": round(exposure_pct, 2),
        "max_drawdown_limit_pct": DEFAULT_MAX_DRAWDOWN_PCT,
        "max_position_limit_pct": DEFAULT_MAX_POSITION_PCT,
        "risk_status": "CRITICAL" if drawdown_pct >= DEFAULT_MAX_DRAWDOWN_PCT else ("WARNING" if drawdown_pct >= DEFAULT_MAX_DRAWDOWN_PCT * 0.7 else "OK"),
    }


@router.post("/check", summary="Pre-Trade Risk Gate Check")
async def risk_check(
    request: RiskCheckRequest,
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    canonical = resolve_canonical(request.symbol)
    snap = await redis_store.get_snapshot(canonical)
    live_price = float(snap.get("last", 0.0)) if snap else 0.0
    current_price = live_price if live_price > 0 else request.entry_price

    state = RiskState(
        current_capital=request.current_capital,
        initial_capital=request.initial_capital,
        position_size=request.position_size,
        entry_price=request.entry_price,
        current_price=current_price,
        max_drawdown_pct=request.max_drawdown_pct,
        max_position_pct=request.max_position_pct,
        max_loss_per_trade_pct=request.max_loss_per_trade_pct,
    )

    result = _engine.check_trade(state, request.requested_quantity)
    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "symbol": request.symbol,
        "allowed": result.allowed,
        "verdict": "ALLOW" if result.allowed else "BLOCK",
        "reason": result.reason,
        "suggested_quantity": result.suggested_quantity,
        "current_drawdown_pct": result.current_drawdown_pct,
        "current_exposure_pct": result.current_exposure_pct,
        "live_price": current_price,
    }


@router.post("/position-size", summary="Calculate Recommended Position Size")
async def calculate_position_size(request: PositionSizeRequest) -> Dict[str, Any]:
    if request.method == "kelly":
        qty = _engine.kelly_size(
            win_rate=request.win_rate,
            avg_win=request.avg_win,
            avg_loss=request.avg_loss,
            capital=request.capital,
            current_price=request.current_price,
        )
    else:
        qty = _engine.fixed_fractional_size(
            capital=request.capital,
            current_price=request.current_price,
            risk_pct=request.risk_pct,
        )

    trade_value = qty * request.current_price
    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "method": request.method,
        "recommended_quantity": qty,
        "trade_value_usd": round(trade_value, 2),
        "risk_pct_of_capital": round((trade_value / request.capital) * 100.0, 2),
    }
