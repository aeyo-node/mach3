from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.analytics.engine import compute_analytics
from swaram.analytics.macro_watchdog import MacroEventWatchdog
from swaram.core.events import CandleEvent
from swaram.core.symbols import resolve_canonical
from swaram.providers.macro.calendar import EconomicCalendarProvider
from swaram.storage.redis import RedisLiveStore
from swaram.storage.repositories.instrument_repo import InstrumentRepository
from swaram.storage.repositories.market_repo import MarketDataRepository

AGENT_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "get_market_snapshot",
        "description": "Get real-time price snapshot, bid/ask, spread, and 24h metrics for a financial instrument.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name (e.g. BTCUSD, EURUSD, XAUUSD)"}
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_technical_indicators",
        "description": "Get quantitative technical indicators (EMA 9/21/50/200, RSI, MACD, ATR, Bollinger, Realized Volatility) for a symbol.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "timeframe": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d"], "default": "1m"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_market_structure",
        "description": "Get institutional market structure analysis (BOS, CHoCH, Fair Value Gaps, Order Blocks, Liquidity Sweeps).",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Symbol name"},
                "timeframe": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "4h", "1d"], "default": "1m"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_macro_risk",
        "description": "Get current macroeconomic event risk window status (NFP, CPI, FOMC, ECB Rate Decisions) and active risk warnings.",
        "parameters": {
            "type": "object",
            "properties": {
                "buffer_minutes": {"type": "integer", "default": 15, "description": "Risk window buffer around high-impact events in minutes"}
            },
        },
    },
]


class AgentToolExecutor:
    """Deterministic tool execution registry for AI Agents."""

    def __init__(self, session: AsyncSession, redis_store: RedisLiveStore):
        self.session = session
        self.redis_store = redis_store

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute named tool with provided arguments."""
        if tool_name == "get_market_snapshot":
            symbol = arguments.get("symbol", "BTCUSD")
            canonical = resolve_canonical(symbol)
            snap = await self.redis_store.get_snapshot(canonical)
            return {"symbol": symbol, "canonical_symbol": canonical, "snapshot": snap}

        elif tool_name == "get_technical_indicators":
            symbol = arguments.get("symbol", "BTCUSD")
            timeframe = arguments.get("timeframe", "1m")
            canonical = resolve_canonical(symbol)
            
            inst_repo = InstrumentRepository(self.session)
            inst = await inst_repo.get_by_canonical(canonical)
            if not inst:
                return {"error": f"Instrument '{canonical}' not found."}

            market_repo = MarketDataRepository(self.session)
            db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)
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
            snapshot = compute_analytics(canonical, timeframe, events)
            return snapshot.to_dict()["indicators"]

        elif tool_name == "get_market_structure":
            symbol = arguments.get("symbol", "BTCUSD")
            timeframe = arguments.get("timeframe", "1m")
            canonical = resolve_canonical(symbol)
            
            inst_repo = InstrumentRepository(self.session)
            inst = await inst_repo.get_by_canonical(canonical)
            if not inst:
                return {"error": f"Instrument '{canonical}' not found."}

            market_repo = MarketDataRepository(self.session)
            db_candles = await market_repo.get_recent_candles(inst.id, timeframe=timeframe, limit=200)
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
            snapshot = compute_analytics(canonical, timeframe, events)
            return snapshot.to_dict()["market_structure"]

        elif tool_name == "get_macro_risk":
            buffer_mins = arguments.get("buffer_minutes", 15)
            provider = EconomicCalendarProvider()
            events = await provider.get_upcoming_events(days_ahead=7)
            watchdog = MacroEventWatchdog(buffer_minutes=buffer_mins)
            return watchdog.evaluate_risk_window(events)

        else:
            return {"error": f"Unknown tool name '{tool_name}'."}
