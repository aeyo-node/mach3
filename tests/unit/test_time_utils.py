from datetime import datetime, timezone
import pytest
from swaram.core.time import (
    calc_latency_ms,
    epoch_ms,
    iso_ist,
    iso_utc,
    now_utc,
    to_ist,
    to_utc,
)


def test_now_utc_aware():
    now = now_utc()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_to_utc_conversions():
    # from naive
    naive = datetime(2026, 8, 21, 12, 0, 0)
    utc_dt = to_utc(naive)
    assert utc_dt.tzinfo == timezone.utc

    # from ISO string
    iso_str = "2026-08-21T12:00:00Z"
    dt = to_utc(iso_str)
    assert dt.year == 2026
    assert dt.hour == 12

    # from timestamp seconds
    dt_sec = to_utc(1724241600)
    assert dt_sec.tzinfo == timezone.utc

    # from timestamp microseconds
    dt_us = to_utc(1724241600000000)
    assert dt_us.tzinfo == timezone.utc


def test_to_ist():
    utc_dt = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    ist_dt = to_ist(utc_dt)
    assert ist_dt.hour == 17
    assert ist_dt.minute == 30  # UTC+5:30


def test_calc_latency_ms():
    t1 = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 21, 12, 0, 1, tzinfo=timezone.utc)
    latency = calc_latency_ms(t1, t2)
    assert latency == 1000.0
