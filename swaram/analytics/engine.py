from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from swaram.analytics.indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_realized_volatility,
    calculate_rsi,
    calculate_sma,
)
from swaram.analytics.structure import (
    MarketStructureResult,
    analyze_market_structure,
)
from swaram.analytics.volume import calculate_volume_profile, calculate_vwap
from swaram.core.events import CandleEvent
from swaram.core.time import iso_ist, iso_utc, now_utc


@dataclass
class AnalyticsSnapshot:
    canonical_symbol: str
    timeframe: str
    timestamp: datetime
    
    # Technical Indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    atr: Optional[float] = None
    
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    
    bollinger_upper: Optional[float] = None
    bollinger_mid: Optional[float] = None
    bollinger_lower: Optional[float] = None
    
    vwap: Optional[float] = None
    realized_vol_24h: Optional[float] = None
    
    # Volume Profile
    poc_price: Optional[float] = None
    vah_price: Optional[float] = None
    val_price: Optional[float] = None
    
    # Market Structure
    market_trend: str = "NEUTRAL"
    latest_event: Optional[Dict[str, Any]] = None
    active_fvgs_count: int = 0
    active_order_blocks_count: int = 0
    recent_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canonical_symbol": self.canonical_symbol,
            "timeframe": self.timeframe,
            "timestamp_utc": iso_utc(self.timestamp),
            "timestamp_ist": iso_ist(self.timestamp),
            "indicators": {
                "rsi": round(self.rsi, 2) if self.rsi is not None else None,
                "macd": round(self.macd, 4) if self.macd is not None else None,
                "macd_signal": round(self.macd_signal, 4) if self.macd_signal is not None else None,
                "macd_hist": round(self.macd_hist, 4) if self.macd_hist is not None else None,
                "atr": round(self.atr, 4) if self.atr is not None else None,
                "ema_9": round(self.ema_9, 2) if self.ema_9 is not None else None,
                "ema_21": round(self.ema_21, 2) if self.ema_21 is not None else None,
                "ema_50": round(self.ema_50, 2) if self.ema_50 is not None else None,
                "ema_200": round(self.ema_200, 2) if self.ema_200 is not None else None,
                "bollinger_upper": round(self.bollinger_upper, 2) if self.bollinger_upper is not None else None,
                "bollinger_mid": round(self.bollinger_mid, 2) if self.bollinger_mid is not None else None,
                "bollinger_lower": round(self.bollinger_lower, 2) if self.bollinger_lower is not None else None,
                "vwap": round(self.vwap, 2) if self.vwap is not None else None,
                "realized_vol_24h": round(self.realized_vol_24h, 4) if self.realized_vol_24h is not None else None,
            },
            "volume_profile": {
                "poc": self.poc_price,
                "vah": self.vah_price,
                "val": self.val_price,
            },
            "market_structure": {
                "trend": self.market_trend,
                "latest_event": self.latest_event,
                "active_fvgs_count": self.active_fvgs_count,
                "active_order_blocks_count": self.active_order_blocks_count,
                "recent_events": self.recent_events,
            },
        }


def compute_analytics(
    canonical_symbol: str,
    timeframe: str,
    candles: List[CandleEvent],
) -> AnalyticsSnapshot:
    """Compute full analytics suite for a given sequence of candles."""
    if not candles:
        return AnalyticsSnapshot(
            canonical_symbol=canonical_symbol,
            timeframe=timeframe,
            timestamp=now_utc(),
        )

    # Sort candles chronologically
    sorted_candles = sorted(candles, key=lambda c: c.timestamp)
    timestamps = [c.timestamp for c in sorted_candles]
    opens = np.array([c.open for c in sorted_candles], dtype=float)
    highs = np.array([c.high for c in sorted_candles], dtype=float)
    lows = np.array([c.low for c in sorted_candles], dtype=float)
    closes = np.array([c.close for c in sorted_candles], dtype=float)
    volumes = np.array([c.volume for c in sorted_candles], dtype=float)

    last_ts = timestamps[-1]

    # Technical Indicators
    rsi_arr = calculate_rsi(closes)
    macd_line, macd_sig, macd_hist = calculate_macd(closes)
    atr_arr = calculate_atr(highs, lows, closes)
    bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(closes)
    
    ema9_arr = calculate_ema(closes, 9)
    ema21_arr = calculate_ema(closes, 21)
    ema50_arr = calculate_ema(closes, 50)
    ema200_arr = calculate_ema(closes, 200)

    vwap_arr = calculate_vwap(closes, highs, lows, volumes)
    rv_24h = calculate_realized_volatility(closes)

    # Volume Profile
    vp_res = calculate_volume_profile(closes, volumes)

    # Market Structure
    ms_res = analyze_market_structure(timestamps, opens, highs, lows, closes)

    def _safe_last(arr: np.ndarray) -> Optional[float]:
        if len(arr) == 0 or np.isnan(arr[-1]):
            return None
        return float(arr[-1])

    latest_evt = ms_res.events[-1] if ms_res.events else None

    # Format recent structure events with UTC/IST timestamps
    formatted_events = []
    for ev in ms_res.events:
        evt_copy = dict(ev)
        if "timestamp" in evt_copy and isinstance(evt_copy["timestamp"], datetime):
            evt_copy["timestamp_utc"] = iso_utc(evt_copy["timestamp"])
            evt_copy["timestamp_ist"] = iso_ist(evt_copy["timestamp"])
            del evt_copy["timestamp"]
        formatted_events.append(evt_copy)

    return AnalyticsSnapshot(
        canonical_symbol=canonical_symbol,
        timeframe=timeframe,
        timestamp=last_ts,
        rsi=_safe_last(rsi_arr),
        macd=_safe_last(macd_line),
        macd_signal=_safe_last(macd_sig),
        macd_hist=_safe_last(macd_hist),
        atr=_safe_last(atr_arr),
        ema_9=_safe_last(ema9_arr),
        ema_21=_safe_last(ema21_arr),
        ema_50=_safe_last(ema50_arr),
        ema_200=_safe_last(ema200_arr),
        bollinger_upper=_safe_last(bb_upper),
        bollinger_mid=_safe_last(bb_mid),
        bollinger_lower=_safe_last(bb_lower),
        vwap=_safe_last(vwap_arr),
        realized_vol_24h=rv_24h,
        poc_price=vp_res.poc_price,
        vah_price=vp_res.vah_price,
        val_price=vp_res.val_price,
        market_trend=ms_res.trend,
        latest_event=latest_evt,
        active_fvgs_count=len(ms_res.active_fvgs),
        active_order_blocks_count=len(ms_res.active_order_blocks),
        recent_events=formatted_events,
    )
