from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from swaram.models.base import Base, TimestampMixin


class OrderflowAnalyticsSnapshot(Base, TimestampMixin):
    """Snapshot table for orderbook depth imbalance, microprice, and spread metrics."""
    __tablename__ = "orderflow_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)

    best_bid: Mapped[float] = mapped_column(Float, nullable=False)
    best_ask: Mapped[float] = mapped_column(Float, nullable=False)
    mid_price: Mapped[float] = mapped_column(Float, nullable=False)
    microprice: Mapped[float] = mapped_column(Float, nullable=False)
    spread: Mapped[float] = mapped_column(Float, nullable=False)
    spread_bps: Mapped[float] = mapped_column(Float, nullable=False)
    
    bid_depth_top20: Mapped[float] = mapped_column(Float, nullable=False)
    ask_depth_top20: Mapped[float] = mapped_column(Float, nullable=False)
    depth_imbalance: Mapped[float] = mapped_column(Float, nullable=False)  # -1.0 to +1.0

    liquidity_walls: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class PositioningRecord(Base, TimestampMixin):
    """Record for derivatives funding rates and open interest regime tracking."""
    __tablename__ = "positioning_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)

    funding_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    annualized_funding_yield: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open_interest: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open_interest_delta_24h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    positioning_regime: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # e.g., "AGGRESSIVE_LONG_BUILDING"
