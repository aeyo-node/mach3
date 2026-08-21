from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.deps import get_redis_store, get_session
from swaram.agents.hermes import HermesContextBuilder
from swaram.agents.tools import AGENT_TOOL_SCHEMAS, AgentToolExecutor
from swaram.analytics.engine import compute_analytics
from swaram.analytics.macro_watchdog import MacroEventWatchdog
from swaram.core.events import CandleEvent
from swaram.core.symbols import resolve_canonical
from swaram.providers.macro.calendar import EconomicCalendarProvider
from swaram.storage.redis import RedisLiveStore
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository

router = APIRouter(prefix="/agent", tags=["AI Multi-Agent Tools & Context Interfaces"])


class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


@router.get("/tools/schema", summary="Get AI Agent Tool Schemas")
async def get_tool_schemas() -> Dict[str, Any]:
    return {
        "total_tools": len(AGENT_TOOL_SCHEMAS),
        "tools": AGENT_TOOL_SCHEMAS,
    }


@router.post("/tools/execute", summary="Execute Agent Tool Deterministically")
async def execute_tool(
    request: ToolExecuteRequest,
    session: AsyncSession = Depends(get_session),
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    executor = AgentToolExecutor(session, redis_store)
    result = await executor.execute(request.tool_name, request.arguments)
    return {
        "tool_name": request.tool_name,
        "arguments": request.arguments,
        "result": result,
    }


@router.get("/context/{symbol}", summary="Get Unified Hermes System Prompt Context for AI Agent")
async def get_hermes_context(
    symbol: str,
    timeframe: str = "1m",
    session: AsyncSession = Depends(get_session),
    redis_store: RedisLiveStore = Depends(get_redis_store),
) -> Dict[str, Any]:
    canonical = resolve_canonical(symbol)
    
    # 1. Snapshot
    snapshot = await redis_store.get_snapshot(canonical)

    # 2. Indicators & Structure
    inst_repo = InstrumentRepository(session)
    inst = await inst_repo.get_by_canonical(canonical)
    
    indicators = None
    market_structure = None
    
    if inst:
        market_repo = MarketDataRepository(session)
        db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)
        if db_candles:
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
            analytics_snap = compute_analytics(canonical, timeframe, events)
            res_dict = analytics_snap.to_dict()
            indicators = res_dict["indicators"]
            market_structure = res_dict["market_structure"]

    # 3. Macro Risk
    macro_provider = EconomicCalendarProvider()
    events_list = await macro_provider.get_upcoming_events(days_ahead=7)
    watchdog = MacroEventWatchdog(buffer_minutes=15)
    macro_risk = watchdog.evaluate_risk_window(events_list)

    # 4. Hermes Formatting
    builder = HermesContextBuilder()
    return builder.build_system_context(
        symbol=symbol,
        canonical_symbol=canonical,
        snapshot=snapshot,
        indicators=indicators,
        market_structure=market_structure,
        macro_risk=macro_risk,
    )
