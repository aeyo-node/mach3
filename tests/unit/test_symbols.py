import pytest
from swaram.core.symbols import (
    parse_canonical,
    resolve_canonical,
    to_canonical,
    to_provider_symbol,
)


def test_parse_canonical():
    sym = parse_canonical("CRYPTO:BTC/USD")
    assert sym.asset_class == "crypto"
    assert sym.base == "BTC"
    assert sym.quote == "USD"
    assert sym.value == "CRYPTO:BTC/USD"


def test_parse_canonical_invalid():
    with pytest.raises(ValueError):
        parse_canonical("BTCUSD")


def test_to_canonical_delta():
    assert to_canonical("delta", "BTCUSD") == "CRYPTO:BTC/USD"
    assert to_canonical("delta", "ETHUSD") == "CRYPTO:ETH/USD"


def test_resolve_canonical():
    assert resolve_canonical("BTCUSD") == "CRYPTO:BTC/USD"
    assert resolve_canonical("BTC/USD") == "CRYPTO:BTC/USD"
    assert resolve_canonical("EURUSD") == "FX:EUR/USD"
    assert resolve_canonical("XAUUSD") == "METAL:XAU/USD"
    assert resolve_canonical("CRYPTO:BTC/USD") == "CRYPTO:BTC/USD"


def test_to_provider_symbol():
    assert to_provider_symbol("CRYPTO:BTC/USD", "delta") == "BTCUSD"
    assert to_provider_symbol("CRYPTO:BTC/USD", "bybit") == "BTCUSDT"
    assert to_provider_symbol("FX:EUR/USD", "ctrader") == "EURUSD"
