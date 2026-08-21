from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PositioningResult:
    funding_rate: Optional[float]
    annualized_yield_pct: Optional[float]
    open_interest: Optional[float]
    open_interest_delta_24h_pct: Optional[float]
    positioning_regime: str
    extreme_funding_warning: bool


def calculate_annualized_funding_yield(funding_rate: float) -> float:
    """Calculate annualized funding yield (assuming 8-hour funding intervals = 3 realizations per day)."""
    return float(funding_rate * 3.0 * 365.0 * 100.0)


def evaluate_positioning_regime(
    price_change_pct: float,
    oi_change_pct: float,
    threshold: float = 0.5,
) -> str:
    """Determine institutional positioning regime based on Price & Open Interest dynamics."""
    if abs(price_change_pct) < threshold and abs(oi_change_pct) < threshold:
        return "CONSOLIDATION"

    if price_change_pct > 0 and oi_change_pct > 0:
        return "AGGRESSIVE_LONG_BUILDING"  # Bullish expansion
    elif price_change_pct < 0 and oi_change_pct > 0:
        return "AGGRESSIVE_SHORT_BUILDING" # Bearish expansion
    elif price_change_pct > 0 and oi_change_pct < 0:
        return "SHORT_COVERING"            # Weak rally
    elif price_change_pct < 0 and oi_change_pct < 0:
        return "LONG_LIQUIDATION"          # Weak selloff

    return "NEUTRAL"


def analyze_positioning(
    funding_rate: Optional[float],
    open_interest: Optional[float],
    open_interest_24h_ago: Optional[float],
    price_24h_change_pct: float = 0.0,
) -> PositioningResult:
    """Analyze derivatives funding yield and Open Interest regime."""
    annualized_yield = (
        calculate_annualized_funding_yield(funding_rate) if funding_rate is not None else None
    )

    oi_delta_pct = None
    if open_interest is not None and open_interest_24h_ago is not None and open_interest_24h_ago > 0:
        oi_delta_pct = ((open_interest - open_interest_24h_ago) / open_interest_24h_ago) * 100.0

    regime = evaluate_positioning_regime(
        price_change_pct=price_24h_change_pct,
        oi_change_pct=oi_delta_pct or 0.0,
    )

    is_extreme = False
    if funding_rate is not None and abs(funding_rate) > 0.0005:  # > 0.05% per 8h
        is_extreme = True

    return PositioningResult(
        funding_rate=round(funding_rate, 6) if funding_rate is not None else None,
        annualized_yield_pct=round(annualized_yield, 2) if annualized_yield is not None else None,
        open_interest=round(open_interest, 2) if open_interest is not None else None,
        open_interest_delta_24h_pct=round(oi_delta_pct, 2) if oi_delta_pct is not None else None,
        positioning_regime=regime,
        extreme_funding_warning=is_extreme,
    )
