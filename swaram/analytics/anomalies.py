from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AnomalyAlert:
    anomaly_type: str
    severity: str
    description: str
    trigger_value: float
    threshold_value: float


def detect_price_spike(
    last_price: float,
    prev_price: float,
    pct_threshold: float = 2.0,
) -> Optional[AnomalyAlert]:
    """Detect flash crash or price spikes (e.g. >2% move in 1 step)."""
    if prev_price <= 0:
        return None

    pct_move = ((last_price - prev_price) / prev_price) * 100.0
    if abs(pct_move) >= pct_threshold:
        severity = "CRITICAL" if abs(pct_move) >= (pct_threshold * 2.0) else "WARNING"
        direction = "SPIKE" if pct_move > 0 else "FLASH CRASH"
        return AnomalyAlert(
            anomaly_type="FLASH_CRASH" if pct_move < 0 else "PRICE_SPIKE",
            severity=severity,
            description=f"Potential {direction} detected: {pct_move:.2f}% price change.",
            trigger_value=round(pct_move, 4),
            threshold_value=pct_threshold,
        )
    return None


def detect_spread_explosion(
    spread: float,
    avg_spread: float,
    multiplier: float = 5.0,
) -> Optional[AnomalyAlert]:
    """Detect bid-ask spread opening up abnormally (e.g. >5x rolling baseline)."""
    if avg_spread <= 0:
        return None

    if spread >= (avg_spread * multiplier):
        severity = "CRITICAL" if spread >= (avg_spread * multiplier * 2.0) else "WARNING"
        multiple = spread / avg_spread
        return AnomalyAlert(
            anomaly_type="SPREAD_EXPLOSION",
            severity=severity,
            description=f"Spread explosion detected: Spread is {multiple:.2f}x average spread.",
            trigger_value=round(spread, 6),
            threshold_value=round(avg_spread * multiplier, 6),
        )
    return None


def detect_imbalance_anomaly(
    imbalance: float,
    threshold: float = 0.85,
) -> Optional[AnomalyAlert]:
    """Detect extreme orderbook depth imbalance (e.g. |I| > 0.85)."""
    if abs(imbalance) >= threshold:
        direction = "buying" if imbalance > 0 else "selling"
        return AnomalyAlert(
            anomaly_type="EXTREME_IMBALANCE",
            severity="WARNING",
            description=f"Extreme orderbook {direction} pressure: Imbalance is {imbalance:.2f}.",
            trigger_value=round(imbalance, 4),
            threshold_value=threshold,
        )
    return None


def detect_volume_anomaly(
    volume: float,
    avg_volume: float,
    multiplier: float = 4.0,
) -> Optional[AnomalyAlert]:
    """Detect volume surges (e.g. volume >4x historical baseline)."""
    if avg_volume <= 0:
        return None

    if volume >= (avg_volume * multiplier):
        multiple = volume / avg_volume
        return AnomalyAlert(
            anomaly_type="VOLUME_SURGE",
            severity="WARNING",
            description=f"Volume surge detected: Volume is {multiple:.2f}x the historical average.",
            trigger_value=round(volume, 2),
            threshold_value=round(avg_volume * multiplier, 2),
        )
    return None
