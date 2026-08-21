from datetime import datetime, timezone
from typing import Optional, Union
import pytz

IST = pytz.timezone("Asia/Kolkata")
UTC = timezone.utc


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def to_utc(dt: Union[datetime, str, int, float]) -> datetime:
    """Convert any input datetime/timestamp to a timezone-aware UTC datetime.
    
    Raises ValueError if input cannot be parsed or is ambiguous.
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            # Assume UTC if naive, but enforce UTC
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    elif isinstance(dt, (int, float)):
        # Support seconds, milliseconds, microseconds
        if dt > 1e14:  # microseconds
            return datetime.fromtimestamp(dt / 1e6, tz=UTC)
        elif dt > 1e11:  # milliseconds
            return datetime.fromtimestamp(dt / 1e3, tz=UTC)
        else:  # seconds
            return datetime.fromtimestamp(dt, tz=UTC)
    elif isinstance(dt, str):
        # Parse ISO string
        parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    raise ValueError(f"Unsupported datetime type: {type(dt)} ({dt})")


def to_ist(dt: datetime) -> datetime:
    """Convert a UTC datetime to Asia/Kolkata timezone."""
    utc_dt = to_utc(dt)
    return utc_dt.astimezone(IST)


def iso_utc(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO 8601 UTC string (e.g. 2026-08-21T11:41:00.000000Z)."""
    target = now_utc() if dt is None else to_utc(dt)
    return target.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def iso_ist(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO 8601 Asia/Kolkata string."""
    target = now_utc() if dt is None else to_utc(dt)
    return to_ist(target).strftime("%Y-%m-%d %H:%M:%S %Z%z")


def epoch_ms(dt: Optional[datetime] = None) -> int:
    """Return epoch timestamp in milliseconds."""
    target = now_utc() if dt is None else to_utc(dt)
    return int(target.timestamp() * 1000)


def from_epoch_us(epoch_us: Union[int, float, str, None]) -> Optional[datetime]:
    """Convert a Unix epoch in microseconds to a UTC datetime. Returns None if input is None/0."""
    if epoch_us is None:
        return None
    val = float(epoch_us)
    if val == 0:
        return None
    return to_utc(val)


def calc_latency_ms(source_time: Union[datetime, int, float, str], received_time: Optional[datetime] = None) -> float:
    """Calculate ingestion latency in milliseconds between source timestamp and received time."""
    src_dt = to_utc(source_time)
    rec_dt = now_utc() if received_time is None else to_utc(received_time)
    delta_sec = (rec_dt - src_dt).total_seconds()
    return max(0.0, delta_sec * 1000.0)
