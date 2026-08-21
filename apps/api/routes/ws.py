import asyncio
import json
import logging
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from swaram.core.symbols import resolve_canonical
from swaram.core.time import iso_ist, iso_utc, now_utc
from swaram.agents.hermes import HermesContextBuilder
from swaram.storage.redis import RedisLiveStore, get_redis

router = APIRouter(tags=["WebSocket Real-Time Streaming"])

logger = logging.getLogger("api.ws")

# Track active WS connection counts per symbol
_active_connections: Dict[str, Set[WebSocket]] = {}


def _register(symbol: str, ws: WebSocket) -> None:
    _active_connections.setdefault(symbol, set()).add(ws)


def _unregister(symbol: str, ws: WebSocket) -> None:
    _active_connections.get(symbol, set()).discard(ws)


async def _send_json_safe(ws: WebSocket, payload: Dict[str, Any]) -> bool:
    """Send JSON payload; return False if connection is broken."""
    try:
        await ws.send_json(payload)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# WS /ws/market/{symbol}  — live price snapshot stream
# ---------------------------------------------------------------------------

@router.websocket("/ws/market/{symbol}")
async def ws_market_stream(websocket: WebSocket, symbol: str) -> None:
    """
    Stream live price snapshots for a given instrument.
    Pushes a new JSON frame every second from Redis.
    """
    canonical = resolve_canonical(symbol)
    await websocket.accept()
    _register(symbol, websocket)
    redis_store = RedisLiveStore(get_redis())

    logger.info(f"WS /ws/market/{symbol} connected")
    try:
        while True:
            snap = await redis_store.get_snapshot(canonical)
            now = now_utc()

            if snap:
                payload: Dict[str, Any] = {
                    "event": "snapshot",
                    "symbol": symbol,
                    "canonical_symbol": canonical,
                    "timestamp_utc": iso_utc(now),
                    "timestamp_ist": iso_ist(now),
                    "last": snap.get("last"),
                    "bid": snap.get("bid"),
                    "ask": snap.get("ask"),
                    "spread": snap.get("spread"),
                    "volume_24h": snap.get("volume_24h"),
                    "change_24h_pct": snap.get("change_24h_pct"),
                }
            else:
                payload = {
                    "event": "waiting",
                    "symbol": symbol,
                    "canonical_symbol": canonical,
                    "timestamp_utc": iso_utc(now),
                    "message": "Data stream initializing…",
                }

            ok = await _send_json_safe(websocket, payload)
            if not ok:
                break

            # Check for any incoming client message (ping / close) without blocking
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                if msg == "ping":
                    await _send_json_safe(websocket, {"event": "pong"})
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        logger.info(f"WS /ws/market/{symbol} disconnected")
    finally:
        _unregister(symbol, websocket)


# ---------------------------------------------------------------------------
# WS /ws/agent/{symbol}  — live Hermes agent context stream
# ---------------------------------------------------------------------------

@router.websocket("/ws/agent/{symbol}")
async def ws_agent_context_stream(websocket: WebSocket, symbol: str) -> None:
    """
    Stream live Hermes agent context (snapshot + indicators + macro) every 5s.
    Intended for AI agents and front-end strategy dashboards.
    """
    canonical = resolve_canonical(symbol)
    await websocket.accept()
    _register(symbol, websocket)
    redis_store = RedisLiveStore(get_redis())
    hermes = HermesContextBuilder()

    logger.info(f"WS /ws/agent/{symbol} connected")
    try:
        while True:
            snap = await redis_store.get_snapshot(canonical)
            now = now_utc()

            context = hermes.build_system_context(
                symbol=symbol,
                canonical_symbol=canonical,
                snapshot=snap or None,
                indicators=None,      # Indicators require DB candles; extended in Phase 10
                market_structure=None,
                macro_risk=None,
            )

            payload = {
                "event": "agent_context",
                "symbol": symbol,
                "canonical_symbol": canonical,
                "timestamp_utc": iso_utc(now),
                "timestamp_ist": iso_ist(now),
                "context_summary": context.get("prompt_context_text", ""),
                "snapshot": context.get("structured_payload", {}).get("snapshot"),
            }

            ok = await _send_json_safe(websocket, payload)
            if not ok:
                break

            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                if msg == "ping":
                    await _send_json_safe(websocket, {"event": "pong"})
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(5.0)

    except WebSocketDisconnect:
        logger.info(f"WS /ws/agent/{symbol} disconnected")
    finally:
        _unregister(symbol, websocket)


# ---------------------------------------------------------------------------
# Helper: count of active WS connections (used by Prometheus in Phase 12)
# ---------------------------------------------------------------------------

def get_active_ws_count() -> int:
    return sum(len(v) for v in _active_connections.values())
