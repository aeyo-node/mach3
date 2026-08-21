from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from swaram.models.base import Base, TimestampMixin
from swaram.core.time import now_utc


class Tick(Base, TimestampMixin):
    __tablename__ = "ticks"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    bid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bid_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ask_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Trade(Base, TimestampMixin):
    __tablename__ = "trades"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    trade_id: Mapped[str] = mapped_column(String(64), primary_key=True, default="")
    price: Mapped[float] = mapped_column(Float, nullable=False)
    size: Mapped[float] = mapped_column(Float, nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)  # "buy", "sell", "unknown"


class Candle(Base, TimestampMixin):
    __tablename__ = "candles"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)  # e.g., "1m", "5m", "1h", "1d"
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trade_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class OrderbookSnapshot(Base, TimestampMixin):
    __tablename__ = "orderbook_snapshots"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    depth: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    best_bid: Mapped[float] = mapped_column(Float, nullable=False)
    best_ask: Mapped[float] = mapped_column(Float, nullable=False)
    spread: Mapped[float] = mapped_column(Float, nullable=False)
    bid_depth: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ask_depth: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    imbalance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    microprice: Mapped[float] = mapped_column(Float, nullable=False)
    payload_optional: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class FundingRate(Base, TimestampMixin):
    __tablename__ = "funding"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    funding_rate: Mapped[float] = mapped_column(Float, nullable=False)
    next_funding_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class OpenInterest(Base, TimestampMixin):
    __tablename__ = "open_interest"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    open_interest: Mapped[float] = mapped_column(Float, nullable=False)
    notional_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
