import json
import pytest
from swaram.core.events import (
    CandleEvent,
    FundingEvent,
    MarkSpotPriceEvent,
    OrderbookEvent,
    TickEvent,
    TradeEvent,
)
from swaram.providers.crypto.delta_ws import DeltaWebSocketProvider


@pytest.fixture
def provider():
    return DeltaWebSocketProvider()


def test_parse_ticker_message(provider):
    raw = json.dumps({
        "type": "v2/ticker",
        "symbol": "BTCUSD",
        "mark_price": "65120.5",
        "spot_price": "65115.0",
        "close": "65125.0",
        "quotes": {
            "best_bid": "65120.0",
            "best_ask": "65125.0",
            "best_bid_size": "2.5",
            "best_ask_size": "3.1",
        },
        "funding_rate": "0.0001",
        "next_funding_realization": 1724241600000000,
        "timestamp": 1724241000000000,
    })

    events = provider._parse_message(raw)
    assert len(events) == 3  # TickEvent, FundingEvent, MarkSpotPriceEvent

    tick = next(e for e in events if isinstance(e, TickEvent))
    assert tick.canonical_symbol == "CRYPTO:BTC/USD"
    assert tick.bid == 65120.0
    assert tick.ask == 65125.0
    assert tick.mid == 65122.5
    assert tick.last == 65125.0

    funding = next(e for e in events if isinstance(e, FundingEvent))
    assert funding.funding_rate == 0.0001

    mark_spot = next(e for e in events if isinstance(e, MarkSpotPriceEvent))
    assert mark_spot.mark_price == 65120.5
    assert mark_spot.spot_price == 65115.0


def test_parse_trades_message(provider):
    raw = json.dumps({
        "type": "all_trades",
        "symbol": "ETHUSD",
        "price": 3450.5,
        "size": 1.2,
        "buyer_role": "taker",
        "seller_role": "maker",
        "id": "trade_999",
        "timestamp": 1724241000000000,
    })

    events = provider._parse_message(raw)
    assert len(events) == 1
    trade = events[0]
    assert isinstance(trade, TradeEvent)
    assert trade.canonical_symbol == "CRYPTO:ETH/USD"
    assert trade.price == 3450.5
    assert trade.size == 1.2
    assert trade.side == "buy"
    assert trade.trade_id == "trade_999"


def test_parse_orderbook_message(provider):
    raw = json.dumps({
        "type": "l2_orderbook",
        "symbol": "BTCUSD",
        "buy": [
            {"price": "65100.0", "size": "10.0"},
            {"price": "65090.0", "size": "5.0"},
        ],
        "sell": [
            {"price": "65110.0", "size": "8.0"},
            {"price": "65120.0", "size": "12.0"},
        ],
        "timestamp": 1724241000000000,
    })

    events = provider._parse_message(raw)
    assert len(events) == 1
    ob = events[0]
    assert isinstance(ob, OrderbookEvent)
    assert ob.canonical_symbol == "CRYPTO:BTC/USD"
    assert ob.best_bid == 65100.0
    assert ob.best_ask == 65110.0
    assert ob.spread == 10.0
    assert ob.bid_depth == 15.0
    assert ob.ask_depth == 20.0
    # Imbalance: (15 - 20) / (15 + 20) = -5 / 35 = -0.142857...
    assert pytest.approx(ob.imbalance, 0.001) == -0.142857
    # Microprice: (65100 * 8 + 65110 * 10) / (10 + 8) = (520800 + 651100) / 18 = 1171900 / 18 = 65105.555...
    assert pytest.approx(ob.microprice, 0.01) == 65105.56


def test_parse_candlestick_message(provider):
    raw = json.dumps({
        "type": "candlestick_1m",
        "symbol": "BTCUSD",
        "candle": [1724241000, 65000.0, 65200.0, 64900.0, 65150.0, 120.5, 45],
    })

    events = provider._parse_message(raw)
    assert len(events) == 1
    candle = events[0]
    assert isinstance(candle, CandleEvent)
    assert candle.canonical_symbol == "CRYPTO:BTC/USD"
    assert candle.timeframe == "1m"
    assert candle.open == 65000.0
    assert candle.high == 65200.0
    assert candle.low == 64900.0
    assert candle.close == 65150.0
    assert candle.volume == 120.5
    assert candle.trade_count == 45
