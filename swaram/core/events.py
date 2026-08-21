from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from swaram.core.time import now_utc, iso_utc, iso_ist, calc_latency_ms


@dataclass
class TickEvent:
    canonical_symbol: str
    provider: str
    timestamp: datetime
    ingested_at: datetime = field(default_factory=now_utc)
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid: Optional[float] = None
    last: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    source_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.mid is None and self.bid is not None and self.ask is not None:
            self.mid = (self.bid + self.ask) / 2.0
        if self.source_timestamp is None:
            self.source_timestamp = self.timestamp

    @property
    def latency_ms(self) -> float:
        return calc_latency_ms(self.timestamp, self.ingested_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "provider": self.provider,
            "timestamp": iso_utc(self.timestamp),
            "timestamp_ist": iso_ist(self.timestamp),
            "ingested_at": iso_utc(self.ingested_at),
            "bid": self.bid,
            "ask": self.ask,
            "mid": self.mid,
            "last": self.last,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
            "latency_ms": round(self.latency_ms, 2),
        }


@dataclass
class TradeEvent:
    canonical_symbol: str
    provider: str
    timestamp: datetime
    price: float
    size: float
    side: str  # "buy" | "sell" | "unknown"
    trade_id: Optional[str] = None
    ingested_at: datetime = field(default_factory=now_utc)

    @property
    def latency_ms(self) -> float:
        return calc_latency_ms(self.timestamp, self.ingested_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "provider": self.provider,
            "timestamp": iso_utc(self.timestamp),
            "timestamp_ist": iso_ist(self.timestamp),
            "ingested_at": iso_utc(self.ingested_at),
            "price": self.price,
            "size": self.size,
            "side": self.side,
            "trade_id": self.trade_id,
            "latency_ms": round(self.latency_ms, 2),
        }


@dataclass
class CandleEvent:
    canonical_symbol: str
    provider: str
    timeframe: str  # "1m", "5m", "15m", "1h", "1d"
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int = 0
    ingested_at: datetime = field(default_factory=now_utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "provider": self.provider,
            "timeframe": self.timeframe,
            "timestamp": iso_utc(self.timestamp),
            "timestamp_ist": iso_ist(self.timestamp),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trade_count": self.trade_count,
        }


@dataclass
class OrderbookEvent:
    canonical_symbol: str
    provider: str
    timestamp: datetime
    depth: int
    best_bid: float
    best_ask: float
    spread: float
    spread_bps: float
    bid_depth: float
    ask_depth: float
    imbalance: float  # (bid_depth - ask_depth) / (bid_depth + ask_depth)
    microprice: float
    bids: List[List[float]] = field(default_factory=list)  # [[price, size], ...]
    asks: List[List[float]] = field(default_factory=list)
    ingested_at: datetime = field(default_factory=now_utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "provider": self.provider,
            "timestamp": iso_utc(self.timestamp),
            "timestamp_ist": iso_ist(self.timestamp),
            "depth": self.depth,
            "best_bid": self.best_bid,
            "best_ask": self.best_ask,
            "spread": self.spread,
            "spread_bps": round(self.spread_bps, 4),
            "bid_depth": round(self.bid_depth, 4),
            "ask_depth": round(self.ask_depth, 4),
            "imbalance": round(self.imbalance, 4),
            "microprice": round(self.microprice, 4),
            "bids": self.bids[:10],
            "asks": self.asks[:10],
        }


@dataclass
class FundingEvent:
    canonical_symbol: str
    provider: str
    timestamp: datetime
    funding_rate: float
    next_funding_time: Optional[datetime] = None
    ingested_at: datetime = field(default_factory=now_utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "provider": self.provider,
            "timestamp": iso_utc(self.timestamp),
            "timestamp_ist": iso_ist(self.timestamp),
            "funding_rate": self.funding_rate,
            "next_funding_time": iso_utc(self.next_funding_time) if self.next_funding_time else None,
        }


@dataclass
class MarkSpotPriceEvent:
    canonical_symbol: str
    provider: str
    timestamp: datetime
    mark_price: Optional[float] = None
    spot_price: Optional[float] = None
    ingested_at: datetime = field(default_factory=now_utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "provider": self.provider,
            "timestamp": iso_utc(self.timestamp),
            "mark_price": self.mark_price,
            "spot_price": self.spot_price,
        }
