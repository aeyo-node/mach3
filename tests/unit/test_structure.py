from datetime import datetime, timedelta, timezone
import numpy as np
import pytest
from swaram.analytics.structure import (
    analyze_market_structure,
    detect_swing_points,
)


def test_detect_swing_points():
    base_time = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    timestamps = [base_time + timedelta(minutes=i) for i in range(10)]
    highs = np.array([10.0, 12.0, 15.0, 11.0, 10.0, 14.0, 18.0, 13.0, 12.0, 11.0], dtype=float)
    lows = np.array([8.0, 9.0, 12.0, 8.0, 7.0, 10.0, 14.0, 9.0, 8.0, 7.0], dtype=float)

    swings = detect_swing_points(timestamps, highs, lows, left_bars=2, right_bars=2)
    assert len(swings) > 0
    # Swing High at index 2 (price 15.0)
    sh_2 = next((s for s in swings if s.index == 2), None)
    assert sh_2 is not None
    assert sh_2.is_high
    assert sh_2.price == 15.0


def test_analyze_market_structure_fvg():
    base_time = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    timestamps = [base_time + timedelta(minutes=i) for i in range(5)]
    opens = np.array([100.0, 105.0, 115.0, 125.0, 120.0], dtype=float)
    highs = np.array([102.0, 110.0, 122.0, 128.0, 122.0], dtype=float)
    lows = np.array([99.0, 104.0, 114.0, 122.0, 118.0], dtype=float)
    closes = np.array([101.0, 109.0, 121.0, 126.0, 119.0], dtype=float)

    # Candle 0 high = 102.0, Candle 2 low = 114.0 -> Bullish FVG gap [102.0, 114.0]
    res = analyze_market_structure(timestamps, opens, highs, lows, closes)
    assert len(res.active_fvgs) >= 1
    fvg = res.active_fvgs[0]
    assert fvg.is_bullish
    assert fvg.low_level == 102.0
    assert fvg.high_level == 114.0
