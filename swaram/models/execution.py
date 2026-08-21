from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from swaram.models.base import Base, TimestampMixin


class AccountBalanceRecord(Base, TimestampMixin):
    """Tracks historical account assets, balances, equity, and margins."""
    __tablename__ = "account_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    asset: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g., USDT, DETC
    balance: Mapped[float] = mapped_column(Float, nullable=False)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    available_margin: Mapped[float] = mapped_column(Float, nullable=False)


class LiveOrderRecord(Base, TimestampMixin):
    """Tracks execution details of live orders submitted by AI agents."""
    __tablename__ = "live_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)

    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    client_order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False)  # buy / sell
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)  # limit / market
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # pending, filled, cancelled, rejected
    filled_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    avg_fill_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
