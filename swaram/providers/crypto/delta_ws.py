import asyncio
import json
import random
from typing import Any, AsyncGenerator, Dict, List, Optional
import websockets
from websockets.exceptions import ConnectionClosed

from swaram.core.events import (
    CandleEvent,
    FundingEvent,
    MarkSpotPriceEvent,
    OrderbookEvent,
    TickEvent,
    TradeEvent,
)
from swaram.core.health import ProviderHealth
from swaram.core.logging import get_logger
from swaram.core.symbols import to_canonical
from swaram.core.time import from_epoch_us, now_utc, to_utc
from swaram.providers.base import BaseMarketDataProvider

logger = get_logger("providers.delta_ws")


class DeltaWebSocketProvider(BaseMarketDataProvider):
    """Resilient Delta Exchange India WebSocket Client for real-time market data."""

    def __init__(
        self,
        ws_url: str = "wss://public-socket.india.delta.exchange",
        symbols: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        heartbeat_interval_sec: int = 15,
        stale_threshold_sec: float = 10.0,
    ):
        self.ws_url = ws_url
        self.symbols = symbols or ["BTCUSD", "ETHUSD"]
        self.channels = channels or [
            "v2/ticker",
            "all_trades",
            "candlestick_1m",
            "l2_orderbook",
            "mark_price",
            "spot_price",
        ]
        self.heartbeat_interval_sec = heartbeat_interval_sec
        self.health = ProviderHealth(provider="delta", stale_threshold_sec=stale_threshold_sec)
        
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=5000)

    @property
    def name(self) -> str:
        return "delta"

    async def connect(self) -> None:
        self._running = True

    async def disconnect(self) -> None:
        self._running = False
        self.health.connected = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info("Delta WebSocket disconnected.")

    async def subscribe(self, symbols: List[str], channels: Optional[List[str]] = None) -> None:
        self.symbols = symbols
        if channels:
            self.channels = channels
        if self._ws and not self._ws.closed:
            sub_msg = self._build_subscription_message(self.symbols, self.channels)
            await self._ws.send(json.dumps(sub_msg))
            logger.info("Sent subscription request to Delta WS", symbols=self.symbols, channels=self.channels)

    def _build_subscription_message(self, symbols: List[str], channels: List[str]) -> Dict[str, Any]:
        return {
            "type": "subscribe",
            "payload": {
                "channels": [{"name": ch, "symbols": symbols} for ch in channels]
            },
        }

    async def _heartbeat_loop(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(self.heartbeat_interval_sec)
                if self._ws and not self._ws.closed:
                    ping_msg = json.dumps({"type": "ping"})
                    await self._ws.send(ping_msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Error in Delta heartbeat ping", error=str(e))

    async def stream_events(self) -> AsyncGenerator[object, None]:
        """Main resilient event generator handling reconnects, backoff, and heartbeats."""
        base_delay = 1.0
        max_delay = 30.0
        delay = base_delay

        while self._running:
            try:
                logger.info("Connecting to Delta Exchange WebSocket...", url=self.ws_url)
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=None,  # We handle application-level ping/pong
                    ping_timeout=10,
                    close_timeout=5,
                ) as ws:
                    self._ws = ws
                    self.health.record_message()
                    delay = base_delay  # reset backoff upon successful connect
                    logger.info("Delta WebSocket connected successfully.")

                    # Start heartbeat background task
                    if self._heartbeat_task:
                        self._heartbeat_task.cancel()
                    self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                    # Subscribe to configured channels
                    sub_msg = self._build_subscription_message(self.symbols, self.channels)
                    await ws.send(json.dumps(sub_msg))
                    logger.info("Delta subscription message sent", symbols=self.symbols)

                    async for message in ws:
                        if not self._running:
                            break
                        try:
                            parsed_events = self._parse_message(message)
                            for ev in parsed_events:
                                yield ev
                        except Exception as parse_err:
                            self.health.record_error(str(parse_err))
                            logger.error("Error parsing Delta WS message", error=str(parse_err))

            except (ConnectionClosed, OSError, Exception) as e:
                self.health.record_reconnect()
                self.health.record_error(str(e))
                if not self._running:
                    break
                jitter = random.uniform(0.5, 1.5)
                sleep_time = min(max_delay, delay * jitter)
                logger.warning(
                    f"Delta WS connection failed: {e}. Reconnecting in {sleep_time:.2f}s...",
                    reconnect_count=self.health.reconnect_count,
                )
                await asyncio.sleep(sleep_time)
                delay = min(max_delay, delay * 2.0)

    def _parse_message(self, raw_message: str) -> List[object]:
        """Parse raw WebSocket text message into normalized domain events."""
        events: List[object] = []
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return events

        msg_type = data.get("type", "")

        # Heartbeat response
        if msg_type in ("pong", "heartbeat"):
            self.health.record_message()
            return events

        # Channel: v2/ticker (L1 quotes, 24h stats, mark/spot price, funding)
        if msg_type in ("v2/ticker", "ticker"):
            events.extend(self._parse_ticker(data))
            return events

        # Channel: all_trades
        if msg_type in ("all_trades", "trades"):
            events.extend(self._parse_trades(data))
            return events

        # Channel: candlestick_1m or other candles
        if "candlestick" in msg_type or msg_type == "candle":
            events.extend(self._parse_candle(data))
            return events

        # Channel: l2_orderbook / l1_orderbook
        if "orderbook" in msg_type:
            events.extend(self._parse_orderbook(data))
            return events

        # Channel: mark_price / spot_price
        if msg_type in ("mark_price", "spot_price"):
            events.extend(self._parse_mark_spot(data))
            return events

        return events

    def _parse_ticker(self, data: Dict[str, Any]) -> List[object]:
        events: List[object] = []
        sym = data.get("symbol", "")
        if not sym:
            return events

        canonical = to_canonical("delta", sym)
        raw_ts = data.get("timestamp")
        src_dt = from_epoch_us(raw_ts) if raw_ts else now_utc()
        self.health.record_message(src_dt)

        quotes = data.get("quotes") or {}
        bid = float(quotes.get("best_bid") or data.get("best_bid") or 0.0) or None
        ask = float(quotes.get("best_ask") or data.get("best_ask") or 0.0) or None
        bid_size = float(quotes.get("best_bid_size") or data.get("best_bid_size") or 0.0) or None
        ask_size = float(quotes.get("best_ask_size") or data.get("best_ask_size") or 0.0) or None
        last = float(data.get("close") or data.get("last_price") or 0.0) or None
        mark = float(data.get("mark_price") or 0.0) or None
        spot = float(data.get("spot_price") or 0.0) or None

        # Create TickEvent
        tick = TickEvent(
            canonical_symbol=canonical,
            provider="delta",
            timestamp=src_dt,
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            last=last,
            source_timestamp=src_dt,
        )
        events.append(tick)

        # Funding rate if available
        funding_rate = data.get("funding_rate")
        if funding_rate is not None:
            next_funding_raw = data.get("next_funding_realization")
            next_funding_dt = from_epoch_us(next_funding_raw) if next_funding_raw else None
            events.append(FundingEvent(
                canonical_symbol=canonical,
                provider="delta",
                timestamp=src_dt,
                funding_rate=float(funding_rate),
                next_funding_time=next_funding_dt,
            ))

        # Mark/spot price
        if mark is not None or spot is not None:
            events.append(MarkSpotPriceEvent(
                canonical_symbol=canonical,
                provider="delta",
                timestamp=src_dt,
                mark_price=mark,
                spot_price=spot,
            ))

        return events

    def _parse_trades(self, data: Dict[str, Any]) -> List[object]:
        events: List[object] = []
        sym = data.get("symbol", "")
        if not sym:
            return events

        canonical = to_canonical("delta", sym)
        raw_ts = data.get("timestamp")
        src_dt = from_epoch_us(raw_ts) if raw_ts else now_utc()
        self.health.record_message(src_dt)

        price = float(data.get("price") or 0.0)
        size = float(data.get("size") or 0.0)
        buyer_role = data.get("buyer_role", "")
        seller_role = data.get("seller_role", "")

        if buyer_role == "taker":
            side = "buy"
        elif seller_role == "taker":
            side = "sell"
        else:
            side = data.get("side", "unknown")

        trade = TradeEvent(
            canonical_symbol=canonical,
            provider="delta",
            timestamp=src_dt,
            price=price,
            size=size,
            side=side,
            trade_id=str(data.get("id") or ""),
        )
        events.append(trade)
        return events

    def _parse_candle(self, data: Dict[str, Any]) -> List[object]:
        events: List[object] = []
        sym = data.get("symbol", "")
        if not sym:
            return events

        canonical = to_canonical("delta", sym)
        candle_data = data.get("candle") or data
        timeframe = "1m"
        if "candlestick_" in data.get("type", ""):
            timeframe = data.get("type", "").replace("candlestick_", "")

        # Format: [timestamp, open, high, low, close, volume]
        if isinstance(candle_data, (list, tuple)) and len(candle_data) >= 6:
            c_ts = to_utc(candle_data[0])
            c_open = float(candle_data[1])
            c_high = float(candle_data[2])
            c_low = float(candle_data[3])
            c_close = float(candle_data[4])
            c_vol = float(candle_data[5])
            c_trades = int(candle_data[6]) if len(candle_data) > 6 else 0
        elif isinstance(candle_data, dict):
            raw_ts = candle_data.get("time") or candle_data.get("timestamp")
            c_ts = from_epoch_us(raw_ts) if raw_ts else now_utc()
            c_open = float(candle_data.get("open", 0))
            c_high = float(candle_data.get("high", 0))
            c_low = float(candle_data.get("low", 0))
            c_close = float(candle_data.get("close", 0))
            c_vol = float(candle_data.get("volume", 0))
            c_trades = int(candle_data.get("trades", 0))
        else:
            return events

        self.health.record_message(c_ts)
        candle = CandleEvent(
            canonical_symbol=canonical,
            provider="delta",
            timeframe=timeframe,
            timestamp=c_ts,
            open=c_open,
            high=c_high,
            low=c_low,
            close=c_close,
            volume=c_vol,
            trade_count=c_trades,
        )
        events.append(candle)
        return events

    def _parse_orderbook(self, data: Dict[str, Any]) -> List[object]:
        events: List[object] = []
        sym = data.get("symbol", "")
        if not sym:
            return events

        canonical = to_canonical("delta", sym)
        raw_ts = data.get("timestamp")
        src_dt = from_epoch_us(raw_ts) if raw_ts else now_utc()
        self.health.record_message(src_dt)

        raw_bids = data.get("buy") or data.get("bids") or []
        raw_asks = data.get("sell") or data.get("asks") or []

        bids = []
        for b in raw_bids:
            if isinstance(b, dict):
                bids.append([float(b.get("price", 0)), float(b.get("size", 0))])
            elif isinstance(b, (list, tuple)) and len(b) >= 2:
                bids.append([float(b[0]), float(b[1])])

        asks = []
        for a in raw_asks:
            if isinstance(a, dict):
                asks.append([float(a.get("price", 0)), float(a.get("size", 0))])
            elif isinstance(a, (list, tuple)) and len(a) >= 2:
                asks.append([float(a[0]), float(a[1])])

        # Sort bids descending, asks ascending
        bids = sorted(bids, key=lambda x: x[0], reverse=True)
        asks = sorted(asks, key=lambda x: x[0])

        if not bids or not asks:
            return events

        best_bid = bids[0][0]
        best_bid_size = bids[0][1]
        best_ask = asks[0][0]
        best_ask_size = asks[0][1]

        spread = max(0.0, best_ask - best_bid)
        mid = (best_bid + best_ask) / 2.0
        spread_bps = (spread / mid * 10000.0) if mid > 0 else 0.0

        bid_depth = sum(b[1] for b in bids[:20])
        ask_depth = sum(a[1] for a in asks[:20])
        total_depth = bid_depth + ask_depth
        imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0.0

        # Microprice calculation
        denom = best_bid_size + best_ask_size
        microprice = (best_bid * best_ask_size + best_ask * best_bid_size) / denom if denom > 0 else mid

        ob_event = OrderbookEvent(
            canonical_symbol=canonical,
            provider="delta",
            timestamp=src_dt,
            depth=min(len(bids), len(asks)),
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            spread_bps=spread_bps,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            imbalance=imbalance,
            microprice=microprice,
            bids=bids[:20],
            asks=asks[:20],
        )
        events.append(ob_event)
        return events

    def _parse_mark_spot(self, data: Dict[str, Any]) -> List[object]:
        events: List[object] = []
        sym = data.get("symbol", "")
        if not sym:
            return events

        canonical = to_canonical("delta", sym)
        raw_ts = data.get("timestamp")
        src_dt = from_epoch_us(raw_ts) if raw_ts else now_utc()
        self.health.record_message(src_dt)

        mark = float(data.get("price") or data.get("mark_price") or 0.0) if data.get("type") == "mark_price" or "mark_price" in data else None
        spot = float(data.get("price") or data.get("spot_price") or 0.0) if data.get("type") == "spot_price" or "spot_price" in data else None

        events.append(MarkSpotPriceEvent(
            canonical_symbol=canonical,
            provider="delta",
            timestamp=src_dt,
            mark_price=mark,
            spot_price=spot,
        ))
        return events
