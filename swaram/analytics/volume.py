from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class VolumeProfileResult:
    poc_price: float
    vah_price: float
    val_price: float
    total_volume: float
    profile_bins: Dict[float, float]  # price_level -> volume


def calculate_vwap(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    volumes: np.ndarray,
) -> np.ndarray:
    """Calculate Volume Weighted Average Price (VWAP)."""
    if len(closes) == 0:
        return np.array([], dtype=float)

    typical_price = (highs + lows + closes) / 3.0
    tp_vol = typical_price * volumes
    cum_tp_vol = np.cumsum(tp_vol)
    cum_vol = np.cumsum(volumes)

    # Prevent division by zero
    cum_vol_safe = np.where(cum_vol == 0, 1e-9, cum_vol)
    vwap = cum_tp_vol / cum_vol_safe
    return vwap


def calculate_volume_profile(
    closes: np.ndarray,
    volumes: np.ndarray,
    num_bins: int = 50,
    value_area_pct: float = 0.70,
) -> VolumeProfileResult:
    """Calculate Volume Profile including Point of Control (POC), Value Area High (VAH), and Low (VAL)."""
    if len(closes) == 0 or np.sum(volumes) == 0:
        return VolumeProfileResult(
            poc_price=0.0,
            vah_price=0.0,
            val_price=0.0,
            total_volume=0.0,
            profile_bins={},
        )

    min_price = np.min(closes)
    max_price = np.max(closes)

    if min_price == max_price:
        return VolumeProfileResult(
            poc_price=float(min_price),
            vah_price=float(min_price),
            val_price=float(min_price),
            total_volume=float(np.sum(volumes)),
            profile_bins={float(min_price): float(np.sum(volumes))},
        )

    counts, bin_edges = np.histogram(closes, bins=num_bins, weights=volumes)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    # Point of Control (POC) = Price level with highest volume
    poc_idx = np.argmax(counts)
    poc_price = float(bin_centers[poc_idx])

    # Value Area Calculation (70% of total volume around POC)
    total_volume = float(np.sum(counts))
    target_va_volume = total_volume * value_area_pct

    # Sort bins by volume descending to accumulate 70% value area
    sorted_indices = np.argsort(counts)[::-1]
    accumulated_vol = 0.0
    va_indices = []

    for idx in sorted_indices:
        accumulated_vol += counts[idx]
        va_indices.append(idx)
        if accumulated_vol >= target_va_volume:
            break

    va_prices = bin_centers[va_indices]
    vah_price = float(np.max(va_prices))
    val_price = float(np.min(va_prices))

    profile_dict = {float(round(p, 4)): float(v) for p, v in zip(bin_centers, counts)}

    return VolumeProfileResult(
        poc_price=poc_price,
        vah_price=vah_price,
        val_price=val_price,
        total_volume=total_volume,
        profile_bins=profile_dict,
    )
