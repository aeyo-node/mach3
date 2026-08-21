from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from swaram.core.time import now_utc, iso_utc, iso_ist, calc_latency_ms


@dataclass
class ProviderHealth:
    provider: str
    connected: bool = False
    last_message_at: Optional[datetime] = None
    messages_received: int = 0
    reconnect_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    last_latency_ms: float = 0.0
    stale_threshold_sec: float = 10.0

    @property
    def age_seconds(self) -> float:
        if self.last_message_at is None:
            return float("inf")
        return (now_utc() - self.last_message_at).total_seconds()

    @property
    def is_stale(self) -> bool:
        if not self.connected:
            return True
        return self.age_seconds > self.stale_threshold_sec

    @property
    def status(self) -> str:
        if not self.connected:
            return "DISCONNECTED"
        if self.is_stale:
            return "STALE"
        if self.error_count > 10:
            return "DEGRADED"
        return "HEALTHY"

    def record_message(self, source_time: Optional[datetime] = None) -> None:
        self.connected = True
        self.last_message_at = now_utc()
        self.messages_received += 1
        if source_time:
            self.last_latency_ms = calc_latency_ms(source_time, self.last_message_at)

    def record_reconnect(self) -> None:
        self.reconnect_count += 1
        self.connected = False

    def record_error(self, err: str) -> None:
        self.error_count += 1
        self.last_error = str(err)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "connected": self.connected,
            "is_stale": self.is_stale,
            "age_seconds": round(self.age_seconds, 2) if self.last_message_at else None,
            "messages_received": self.messages_received,
            "reconnect_count": self.reconnect_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_latency_ms": round(self.last_latency_ms, 2),
            "last_message_at": iso_utc(self.last_message_at) if self.last_message_at else None,
            "last_message_at_ist": iso_ist(self.last_message_at) if self.last_message_at else None,
        }
