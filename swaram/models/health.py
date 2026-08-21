from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from swaram.models.base import Base
from swaram.core.time import now_utc


class ProviderHealthRecord(Base):
    __tablename__ = "provider_health_records"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, default=now_utc)
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    message_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
