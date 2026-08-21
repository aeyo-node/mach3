from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from swaram.models.base import Base, TimestampMixin
from swaram.core.time import now_utc


class MacroEvent(Base, TimestampMixin):
    """Database model for macroeconomic calendar releases and central bank announcements."""
    __tablename__ = "macro_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(16), index=True, nullable=False)  # e.g., "US", "EU", "GB", "JP"
    event_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)  # e.g., "Non-Farm Payrolls", "CPI YoY", "FOMC Rate Decision"
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)     # "EMPLOYMENT", "INFLATION", "CENTRAL_BANK"
    
    impact_level: Mapped[str] = mapped_column(String(16), index=True, nullable=False)  # "HIGH", "MEDIUM", "LOW"
    
    actual: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    forecast: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    previous: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)  # "K", "%", "B"
    
    source: Mapped[str] = mapped_column(String(64), default="calendar_feed", nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
