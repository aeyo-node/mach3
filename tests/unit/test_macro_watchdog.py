from datetime import datetime, timedelta, timezone
from swaram.analytics.macro_watchdog import MacroEventWatchdog


def test_macro_watchdog_active_risk_window():
    now = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)
    events = [
        {
            "country": "US",
            "event_name": "Non-Farm Payrolls",
            "impact_level": "HIGH",
            "timestamp": (now + timedelta(minutes=5)).isoformat(),
        }
    ]

    watchdog = MacroEventWatchdog(buffer_minutes=15)
    res = watchdog.evaluate_risk_window(events, current_time=now)
    assert res["is_high_risk_window"] is True
    assert len(res["active_risk_events"]) == 1


def test_macro_watchdog_safe_window():
    now = datetime(2026, 8, 21, 14, 0, 0, tzinfo=timezone.utc)
    events = [
        {
            "country": "US",
            "event_name": "Non-Farm Payrolls",
            "impact_level": "HIGH",
            "timestamp": (now + timedelta(hours=3)).isoformat(),
        }
    ]

    watchdog = MacroEventWatchdog(buffer_minutes=15)
    res = watchdog.evaluate_risk_window(events, current_time=now)
    assert res["is_high_risk_window"] is False
    assert len(res["active_risk_events"]) == 0
