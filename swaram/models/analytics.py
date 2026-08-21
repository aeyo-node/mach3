from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from swaram.models.base import Base, TimestampMixin
from swaram.core.time import now_utc


class MarketStructureEvent(Base, TimestampMixin):
    """Database model for persisting market structure observations (BOS, CHoCH, FVG, Sweeps, Order Blocks)."""
    __tablename__ = "market_structure_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), index=True, nullable=False)
    
    event_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # "BOS", "CHOCH", "FVG", "SWEEP", "ORDER_BLOCK"
    direction: Mapped[str] = mapped_column(String(16), index=True, nullable=False)   # "BULLISH", "BEARISH"
    price_level: Mapped[float] = mapped_column(Float, nullable=False)
    boundary_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    boundary_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    is_mitigated: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    mitigated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    payload_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class IndicatorSnapshot(Base, TimestampMixin):
    """Snapshot table for calculated technical indicators."""
    __tablename__ = "indicator_snapshots"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True, default="engine")

    rsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd_signal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macd_hist: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    atr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    ema_9: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ema_21: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ema_50: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ema_200: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    bollinger_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bollinger_mid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bollinger_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    vwap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    realized_vol_24h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
