from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class SwingPoint:
    index: int
    timestamp: datetime
    price: float
    is_high: bool  # True = Swing High, False = Swing Low


@dataclass
class FVGZone:
    timestamp: datetime
    high_level: float
    low_level: float
    is_bullish: bool
    is_mitigated: bool = False
    mitigated_at: Optional[datetime] = None


@dataclass
class OrderBlockZone:
    timestamp: datetime
    high_level: float
    low_level: float
    is_bullish: bool
    is_mitigated: bool = False


@dataclass
class MarketStructureResult:
    trend: str  # "BULLISH" | "BEARISH" | "NEUTRAL"
    swings: List[SwingPoint] = field(default_factory=list)
    active_fvgs: List[FVGZone] = field(default_factory=list)
    active_order_blocks: List[OrderBlockZone] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)  # BOS, CHoCH, Sweeps


def detect_swing_points(
    timestamps: List[datetime],
    highs: np.ndarray,
    lows: np.ndarray,
    left_bars: int = 2,
    right_bars: int = 2,
) -> List[SwingPoint]:
    """Detect fractal swing highs and swing lows."""
    swings: List[SwingPoint] = []
    n = len(highs)
    if n < left_bars + right_bars + 1:
        return swings

    for i in range(left_bars, n - right_bars):
        # Swing High check
        is_swing_high = True
        for j in range(i - left_bars, i + right_bars + 1):
            if j != i and highs[j] >= highs[i]:
                is_swing_high = False
                break
        if is_swing_high:
            swings.append(SwingPoint(index=i, timestamp=timestamps[i], price=float(highs[i]), is_high=True))

        # Swing Low check
        is_swing_low = True
        for j in range(i - left_bars, i + right_bars + 1):
            if j != i and lows[j] <= lows[i]:
                is_swing_low = False
                break
        if is_swing_low:
            swings.append(SwingPoint(index=i, timestamp=timestamps[i], price=float(lows[i]), is_high=False))

    return sorted(swings, key=lambda s: s.index)


def analyze_market_structure(
    timestamps: List[datetime],
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    left_bars: int = 2,
    right_bars: int = 2,
) -> MarketStructureResult:
    """Analyze complete market structure: Swings, BOS, CHoCH, FVGs, Sweeps, Order Blocks."""
    swings = detect_swing_points(timestamps, highs, lows, left_bars, right_bars)
    
    current_trend = "NEUTRAL"
    last_swing_high: Optional[SwingPoint] = None
    last_swing_low: Optional[SwingPoint] = None
    
    events: List[Dict[str, Any]] = []
    active_fvgs: List[FVGZone] = []
    active_order_blocks: List[OrderBlockZone] = []

    n = len(closes)
    if n < 3:
        return MarketStructureResult(trend=current_trend, swings=swings)

    # 1. Detect FVGs (3-candle patterns)
    for i in range(2, n):
        # Bullish FVG: low of candle i > high of candle i-2
        if lows[i] > highs[i - 2]:
            active_fvgs.append(FVGZone(
                timestamp=timestamps[i],
                high_level=float(lows[i]),
                low_level=float(highs[i - 2]),
                is_bullish=True,
            ))
        # Bearish FVG: high of candle i < low of candle i-2
        elif highs[i] < lows[i - 2]:
            active_fvgs.append(FVGZone(
                timestamp=timestamps[i],
                high_level=float(lows[i - 2]),
                low_level=float(highs[i]),
                is_bullish=False,
            ))

    # Check FVG mitigations
    for fvg in active_fvgs:
        for i in range(2, n):
            if timestamps[i] > fvg.timestamp:
                if fvg.is_bullish and lows[i] <= fvg.high_level:
                    fvg.is_mitigated = True
                    fvg.mitigated_at = timestamps[i]
                    break
                elif not fvg.is_bullish and highs[i] >= fvg.low_level:
                    fvg.is_mitigated = True
                    fvg.mitigated_at = timestamps[i]
                    break

    # 2. Track Swings and Detect BOS / CHoCH / Sweeps
    for i in range(n):
        # Update last known swing high / low up to current index
        current_swings = [s for s in swings if s.index < i]
        sh_list = [s for s in current_swings if s.is_high]
        sl_list = [s for s in current_swings if not s.is_high]
        
        last_sh = sh_list[-1] if sh_list else None
        last_sl = sl_list[-1] if sl_list else None

        current_close = closes[i]
        current_high = highs[i]
        current_low = lows[i]
        current_time = timestamps[i]

        # Check Liquidity Sweep (Wick beyond swing level, close within)
        if last_sh and current_high > last_sh.price and current_close < last_sh.price:
            events.append({
                "type": "SWEEP",
                "direction": "BEARISH",
                "timestamp": current_time,
                "price_level": last_sh.price,
                "detail": "High swept above previous swing high but closed below.",
            })

        if last_sl and current_low < last_sl.price and current_close > last_sl.price:
            events.append({
                "type": "SWEEP",
                "direction": "BULLISH",
                "timestamp": current_time,
                "price_level": last_sl.price,
                "detail": "Low swept below previous swing low but closed above.",
            })

        # Check BOS / CHoCH
        if last_sh and current_close > last_sh.price:
            if current_trend == "BULLISH":
                events.append({
                    "type": "BOS",
                    "direction": "BULLISH",
                    "timestamp": current_time,
                    "price_level": last_sh.price,
                })
            else:
                current_trend = "BULLISH"
                events.append({
                    "type": "CHOCH",
                    "direction": "BULLISH",
                    "timestamp": current_time,
                    "price_level": last_sh.price,
                })
                # Bullish OB is the last bearish candle before this breakout
                if i >= 1:
                    active_order_blocks.append(OrderBlockZone(
                        timestamp=timestamps[i - 1],
                        high_level=float(highs[i - 1]),
                        low_level=float(lows[i - 1]),
                        is_bullish=True,
                    ))

        elif last_sl and current_close < last_sl.price:
            if current_trend == "BEARISH":
                events.append({
                    "type": "BOS",
                    "direction": "BEARISH",
                    "timestamp": current_time,
                    "price_level": last_sl.price,
                })
            else:
                current_trend = "BEARISH"
                events.append({
                    "type": "CHOCH",
                    "direction": "BEARISH",
                    "timestamp": current_time,
                    "price_level": last_sl.price,
                })
                # Bearish OB is the last bullish candle before this breakout
                if i >= 1:
                    active_order_blocks.append(OrderBlockZone(
                        timestamp=timestamps[i - 1],
                        high_level=float(highs[i - 1]),
                        low_level=float(lows[i - 1]),
                        is_bullish=False,
                    ))

    unmitigated_fvgs = [f for f in active_fvgs if not f.is_mitigated]

    return MarketStructureResult(
        trend=current_trend,
        swings=swings,
        active_fvgs=unmitigated_fvgs,
        active_order_blocks=active_order_blocks[-10:],  # keep recent OBs
        events=events[-20:],  # keep recent events
    )
