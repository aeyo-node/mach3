import pytest
from swaram.telemetry.prometheus import METRICS


def test_prometheus_custom_metrics():
    # Verify lightweight metrics interface incrementing/collecting
    METRICS.tick_count.labels(provider="delta", symbol="BTCUSD").inc(5)
    collected = METRICS.tick_count.collect()
    assert "provider=delta,symbol=BTCUSD" in collected
    assert collected["provider=delta,symbol=BTCUSD"] == 5.0

    METRICS.ws_connections.set(12)
    assert METRICS.ws_connections.collect().get("default") == 12.0
