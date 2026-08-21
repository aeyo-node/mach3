from swaram.agents.hermes import HermesContextBuilder


def test_hermes_context_builder():
    builder = HermesContextBuilder()
    snapshot = {"last": 65000.0, "bid": 64995.0, "ask": 65005.0, "spread": 10.0}
    indicators = {"rsi": 55.4, "ema_9": 64900.0, "ema_21": 64800.0}
    market_structure = {"trend": "BULLISH", "active_fvgs_count": 2}
    macro_risk = {"is_high_risk_window": False}

    res = builder.build_system_context(
        symbol="BTCUSD",
        canonical_symbol="CRYPTO:BTC/USD",
        snapshot=snapshot,
        indicators=indicators,
        market_structure=market_structure,
        macro_risk=macro_risk,
    )

    assert res["symbol"] == "BTCUSD"
    assert "prompt_context_text" in res
    text = res["prompt_context_text"]
    assert "SWRAM MARKET INTELLIGENCE STATE" in text
    assert "65000.0" in text
    assert "BULLISH" in text
