from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from swaram.models.base import Base, TimestampMixin


class MarketAnomalyRecord(Base, TimestampMixin):
    """Stores detected market anomalies (flash crashes, spread explosions, volume surges)."""
    __tablename__ = "market_anomaly_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(Integer, ForeignKey("instruments.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)

    anomaly_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SPREAD_EXPLOSION, FLASH_CRASH, etc.
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # INFO, WARNING, CRITICAL
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    trigger_value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)
