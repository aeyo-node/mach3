from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from swaram.core.time import iso_ist, iso_utc, now_utc, to_utc


class MacroEventWatchdog:
    """Watchdog for detecting high-impact macroeconomic event risk windows."""

    def __init__(self, buffer_minutes: int = 15):
        self.buffer_minutes = buffer_minutes

    def evaluate_risk_window(
        self,
        events: List[Dict[str, Any]],
        current_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = now_utc() if current_time is None else to_utc(current_time)
        active_risk_events = []

        for evt in events:
            impact = evt.get("impact_level", "LOW")
            if impact != "HIGH":
                continue

            evt_ts_raw = evt.get("timestamp")
            if not evt_ts_raw:
                continue

            evt_dt = to_utc(evt_ts_raw)
            window_start = evt_dt - timedelta(minutes=self.buffer_minutes)
            window_end = evt_dt + timedelta(minutes=self.buffer_minutes)

            if window_start <= now <= window_end:
                active_risk_events.append({
                    "event_name": evt.get("event_name"),
                    "country": evt.get("country"),
                    "category": evt.get("category"),
                    "event_time_utc": iso_utc(evt_dt),
                    "event_time_ist": iso_ist(evt_dt),
                    "minutes_delta": round((evt_dt - now).total_seconds() / 60.0, 1),
                })

        is_high_risk = len(active_risk_events) > 0

        return {
            "is_high_risk_window": is_high_risk,
            "buffer_minutes": self.buffer_minutes,
            "active_risk_events": active_risk_events,
            "evaluated_at_utc": iso_utc(now),
            "evaluated_at_ist": iso_ist(now),
        }
