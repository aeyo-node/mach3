from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import numpy as np


@dataclass
class OrderbookAnalyticsResult:
    best_bid: float
    best_ask: float
    mid_price: float
    microprice: float
    spread: float
    spread_bps: float
    bid_depth_top20: float
    ask_depth_top20: float
    depth_imbalance: float  # Range: -1.0 (pure ask/sell pressure) to +1.0 (pure bid/buy pressure)
    liquidity_walls: Dict[str, Any]


def calculate_microprice(
    best_bid: float,
    best_bid_size: float,
    best_ask: float,
    best_ask_size: float,
) -> float:
    """Calculate volume-weighted microprice."""
    denom = best_bid_size + best_ask_size
    if denom == 0:
        return (best_bid + best_ask) / 2.0
    return float((best_bid * best_ask_size + best_ask * best_bid_size) / denom)


def calculate_depth_imbalance(
    bids: List[List[float]],
    asks: List[List[float]],
    depth_levels: int = 20,
) -> Tuple[float, float, float]:
    """Calculate cumulative bid depth, ask depth, and depth imbalance ratio."""
    bid_depth = sum(b[1] for b in bids[:depth_levels]) if bids else 0.0
    ask_depth = sum(a[1] for a in asks[:depth_levels]) if asks else 0.0
    total = bid_depth + ask_depth

    if total == 0:
        return 0.0, 0.0, 0.0

    imbalance = (bid_depth - ask_depth) / total
    return float(bid_depth), float(ask_depth), float(imbalance)


def detect_liquidity_walls(
    bids: List[List[float]],
    asks: List[List[float]],
    wall_threshold_multiplier: float = 3.0,
) -> Dict[str, Any]:
    """Detect unusually large limit order walls in top orderbook levels."""
    if not bids or not asks:
        return {"bid_walls": [], "ask_walls": []}

    avg_bid_size = np.mean([b[1] for b in bids[:20]]) if bids else 0.0
    avg_ask_size = np.mean([a[1] for a in asks[:20]]) if asks else 0.0

    bid_walls = [
        {"price": b[0], "size": b[1], "multiple": round(b[1] / avg_bid_size, 2)}
        for b in bids[:20]
        if avg_bid_size > 0 and b[1] >= (avg_bid_size * wall_threshold_multiplier)
    ]

    ask_walls = [
        {"price": a[0], "size": a[1], "multiple": round(a[1] / avg_ask_size, 2)}
        for a in asks[:20]
        if avg_ask_size > 0 and a[1] >= (avg_ask_size * wall_threshold_multiplier)
    ]

    return {
        "bid_walls": bid_walls,
        "ask_walls": ask_walls,
    }


def analyze_orderbook_depth(
    bids: List[List[float]],
    asks: List[List[float]],
) -> OrderbookAnalyticsResult:
    """Analyze L2 Orderbook depth, microprice, imbalance, and liquidity walls."""
    if not bids or not asks:
        return OrderbookAnalyticsResult(
            best_bid=0.0,
            best_ask=0.0,
            mid_price=0.0,
            microprice=0.0,
            spread=0.0,
            spread_bps=0.0,
            bid_depth_top20=0.0,
            ask_depth_top20=0.0,
            depth_imbalance=0.0,
            liquidity_walls={"bid_walls": [], "ask_walls": []},
        )

    best_bid = float(bids[0][0])
    best_bid_size = float(bids[0][1])
    best_ask = float(asks[0][0])
    best_ask_size = float(asks[0][1])

    mid = (best_bid + best_ask) / 2.0
    spread = max(0.0, best_ask - best_bid)
    spread_bps = (spread / mid * 10000.0) if mid > 0 else 0.0

    microprice = calculate_microprice(best_bid, best_bid_size, best_ask, best_ask_size)
    bid_depth, ask_depth, imbalance = calculate_depth_imbalance(bids, asks)
    walls = detect_liquidity_walls(bids, asks)

    return OrderbookAnalyticsResult(
        best_bid=best_bid,
        best_ask=best_ask,
        mid_price=float(round(mid, 4)),
        microprice=float(round(microprice, 4)),
        spread=float(round(spread, 4)),
        spread_bps=float(round(spread_bps, 2)),
        bid_depth_top20=float(round(bid_depth, 4)),
        ask_depth_top20=float(round(ask_depth, 4)),
        depth_imbalance=float(round(imbalance, 4)),
        liquidity_walls=walls,
    )
