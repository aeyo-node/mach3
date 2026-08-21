import pytest
from swaram.analytics.orderbook import (
    analyze_orderbook_depth,
    calculate_depth_imbalance,
    calculate_microprice,
)


def test_calculate_microprice():
    # Equal sizes -> Microprice equals Mid price
    mp1 = calculate_microprice(65000.0, 10.0, 65010.0, 10.0)
    assert mp1 == 65005.0

    # More ask size -> Microprice leans towards Bid
    mp2 = calculate_microprice(65000.0, 10.0, 65010.0, 90.0)
    assert mp2 == 65001.0


def test_calculate_depth_imbalance():
    bids = [[65000.0, 100.0], [64990.0, 50.0]]
    asks = [[65010.0, 20.0], [65020.0, 30.0]]

    b_depth, a_depth, imbalance = calculate_depth_imbalance(bids, asks)
    assert b_depth == 150.0
    assert a_depth == 50.0
    assert pytest.approx(imbalance, 0.01) == 0.5  # (150 - 50) / 200 = +0.5


def test_analyze_orderbook_depth():
    bids = [[65000.0, 10.0], [64990.0, 50.0]]
    asks = [[65010.0, 10.0], [65020.0, 50.0]]

    res = analyze_orderbook_depth(bids, asks)
    assert res.best_bid == 65000.0
    assert res.best_ask == 65010.0
    assert res.mid_price == 65005.0
    assert res.spread == 10.0
