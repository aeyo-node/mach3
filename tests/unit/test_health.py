import time
from datetime import datetime, timedelta, timezone
from swaram.core.health import ProviderHealth
from swaram.core.time import now_utc


def test_provider_health_initial():
    health = ProviderHealth(provider="delta")
    assert not health.connected
    assert health.is_stale
    assert health.status == "DISCONNECTED"


def test_provider_health_connected_and_healthy():
    health = ProviderHealth(provider="delta", stale_threshold_sec=5.0)
    health.record_message()
    assert health.connected
    assert not health.is_stale
    assert health.status == "HEALTHY"
    assert health.messages_received == 1


def test_provider_health_stale():
    health = ProviderHealth(provider="delta", stale_threshold_sec=1.0)
    health.connected = True
    # Simulate message from 10 seconds ago
    health.last_message_at = now_utc() - timedelta(seconds=10)
    assert health.is_stale
    assert health.status == "STALE"


def test_provider_health_reconnect():
    health = ProviderHealth(provider="delta")
    health.record_reconnect()
    assert health.reconnect_count == 1
    assert not health.connected
