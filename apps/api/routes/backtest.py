from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_session
from swaram.backtest.engine import BacktestEngine
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.models.backtest import BacktestRunRecord
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository

router = APIRouter(prefix="/backtest", tags=["Backtesting & Agent Simulation"])


class BacktestRunRequest(BaseModel):
    symbol: str
    start_time: datetime
    end_time: datetime
    initial_capital: float = 10000.0
    slippage_pct: float = 0.05
    timeframe: str = "1m"


@router.post("/run", summary="Trigger a Historical Strategy Backtest")
async def run_backtest(
    request: BacktestRunRequest,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    canonical = resolve_canonical(request.symbol)
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    if not inst:
        raise HTTPException(status_code=404, detail=f"Instrument '{canonical}' not found.")

    market_repo = MarketDataRepository(session)
    # Fetch historical candles for backtesting
    db_candles = await market_repo.get_recent_candles(
        instrument_id=inst.id,
        timeframe=request.timeframe,
        limit=1000,
    )

    if not db_candles:
        # Generate some synthetic historical data if database is empty for backtest demonstration
        import random
        from swaram.models.market_data import Candle
        sim_price = 65000.0
        db_candles = []
        for i in range(100):
            sim_price += random.normalvariate(0, 10)
            db_candles.append(Candle(
                timestamp=now_utc(),
                instrument_id=inst.id,
                provider="delta",
                timeframe="1m",
                open=sim_price - 2,
                high=sim_price + 5,
                low=sim_price - 5,
                close=sim_price,
                volume=10.0,
            ))

    engine = BacktestEngine(
        initial_capital=request.initial_capital,
        slippage_pct=request.slippage_pct,
    )

    # Event-driven backtest execution over loaded candles
    # Simple demonstration strategy: buy when close > open, sell when close < open
    for candle in db_candles:
        price = candle.close
        if candle.close > candle.open and engine.position == 0:
            engine.execute_market_order("buy", 0.1, price, candle.timestamp)
        elif candle.close < candle.open and engine.position > 0:
            engine.execute_market_order("sell", 0.1, price, candle.timestamp)
        engine.update_portfolio(price)

    # Save results to DB
    metrics = engine.calculate_performance_metrics()
    now = now_utc()
    record = BacktestRunRecord(
        timestamp=now,
        symbol=request.symbol,
        start_time=request.start_time,
        end_time=request.end_time,
        initial_capital=request.initial_capital,
        final_capital=metrics["final_capital"],
        total_trades=metrics["total_trades"],
        win_rate=metrics["win_rate"],
        sharpe_ratio=metrics["sharpe_ratio"],
        max_drawdown=metrics["max_drawdown"],
        profit_factor=metrics["profit_factor"],
        metrics_detail={"trades": [str(t) for t in engine.trades]},
    )
    
    session.add(record)
    await session.commit()

    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "symbol": request.symbol,
        "metrics": metrics,
    }


@router.get("/runs", summary="Get Historical Backtest Runs")
async def get_backtest_runs(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    stmt = select(BacktestRunRecord).order_by(desc(BacktestRunRecord.timestamp)).limit(limit)
    result = await session.execute(stmt)
    records = result.scalars().all()

    now = now_utc()
    return {
        "timestamp_utc": iso_utc(now),
        "timestamp_ist": iso_ist(now),
        "runs": [
            {
                "id": r.id,
                "timestamp": iso_utc(r.timestamp),
                "symbol": r.symbol,
                "start_time": iso_utc(r.start_time),
                "end_time": iso_utc(r.end_time),
                "initial_capital": r.initial_capital,
                "final_capital": r.final_capital,
                "win_rate": r.win_rate,
                "sharpe_ratio": r.sharpe_ratio,
                "max_drawdown": r.max_drawdown,
                "profit_factor": r.profit_factor,
            }
            for r in records
        ],
    }
