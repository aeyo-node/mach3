from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from apps.api.deps import get_redis_store, get_session
from apps.api.main import create_app
from swaram.models.instrument import Instrument


@pytest.fixture
def mock_redis_store():
    mock = MagicMock()
    mock.client = MagicMock()
    mock.client.ping = AsyncMock(return_value=True)
    mock.get_all_provider_health = AsyncMock(return_value=[
        {
            "provider": "delta",
            "status": "HEALTHY",
            "connected": True,
            "is_stale": False,
            "messages_received": 150,
            "last_latency_ms": 12.5,
        }
    ])
    mock.get_provider_health = AsyncMock(return_value={
        "provider": "delta",
        "status": "HEALTHY",
        "connected": True,
        "is_stale": False,
    })
    mock.get_snapshot = AsyncMock(return_value={
        "bid": 65120.0,
        "ask": 65125.0,
        "mid": 65122.5,
        "last": 65125.0,
        "best_bid": 65120.0,
        "best_ask": 65125.0,
        "spread": 5.0,
        "spread_bps": 0.77,
        "book_imbalance": 0.15,
        "microprice": 65123.0,
        "funding_rate": 0.0001,
        "mark_price": 65120.5,
        "spot_price": 65115.0,
    })
    return mock


@pytest.fixture
def mock_db_session():
    mock = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar.return_value = 1
    mock.execute.return_value = mock_res
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["database"] == "connected"
    assert data["components"]["redis"] == "connected"
    assert "timestamp_utc" in data
    assert "timestamp_ist" in data


def test_providers_health_endpoint(test_client):
    response = test_client.get("/health/providers")
    assert response.status_code == 200
    data = response.json()
    assert data["all_providers_healthy"] is True
    assert len(data["providers"]) == 1
    assert data["providers"][0]["provider"] == "delta"


def test_market_snapshot_endpoint(test_client):
    response = test_client.get("/market/BTCUSD")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_symbol"] == "CRYPTO:BTC/USD"
    assert data["snapshot"]["bid"] == 65120.0
    assert data["snapshot"]["ask"] == 65125.0
    assert data["snapshot"]["spread"] == 5.0
