"""
Integration tests for WebSocket streaming endpoints.
Uses FastAPI's TestClient with websocket_connect context manager.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.deps import get_redis_store
from apps.api.main import create_app


@pytest.fixture
def mock_redis_store():
    mock = MagicMock()
    mock.get_snapshot = AsyncMock(return_value={
        "last": 65432.10,
        "bid": 65430.00,
        "ask": 65434.20,
        "spread": 4.20,
        "volume_24h": 1234.56,
        "change_24h_pct": 1.23,
    })
    return mock


@pytest.fixture
def test_client(mock_redis_store):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    return TestClient(app)


def test_ws_market_stream_connects_and_receives_snapshot(test_client, mock_redis_store):
    """WS /ws/market/BTCUSD should send a snapshot frame and disconnect gracefully."""
    with patch("apps.api.routes.ws.get_redis") as mock_get_redis, \
         patch("apps.api.routes.ws.RedisLiveStore") as MockStore:
        instance = MockStore.return_value
        instance.get_snapshot = AsyncMock(return_value={
            "last": 65432.10,
            "bid": 65430.00,
            "ask": 65434.20,
            "spread": 4.20,
        })

        with test_client.websocket_connect("/ws/market/BTCUSD") as ws:
            data = ws.receive_json()
            assert data["event"] in ("snapshot", "waiting")
            assert data["symbol"] == "BTCUSD"
            assert data["canonical_symbol"] == "CRYPTO:BTC/USD"


def test_ws_agent_context_stream_connects_and_receives_context(test_client):
    """WS /ws/agent/EURUSD should send an agent_context frame."""
    with patch("apps.api.routes.ws.get_redis"), \
         patch("apps.api.routes.ws.RedisLiveStore") as MockStore:
        instance = MockStore.return_value
        instance.get_snapshot = AsyncMock(return_value={})

        with test_client.websocket_connect("/ws/agent/EURUSD") as ws:
            data = ws.receive_json()
            assert data["event"] == "agent_context"
            assert "context_summary" in data
