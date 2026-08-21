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
    return mock


@pytest.fixture
def mock_db_session():
    mock = AsyncMock()
    instruments = [
        Instrument(id=1, canonical_symbol="CRYPTO:BTC/USD", asset_class="crypto", base_asset="BTC", quote_asset="USD", venue="delta", provider_symbol="BTCUSD"),
        Instrument(id=2, canonical_symbol="FX:EUR/USD", asset_class="fx", base_asset="EUR", quote_asset="USD", venue="ctrader", provider_symbol="EURUSD"),
        Instrument(id=3, canonical_symbol="METAL:XAU/USD", asset_class="metal", base_asset="XAU", quote_asset="USD", venue="ctrader", provider_symbol="XAUUSD"),
    ]
    res = MagicMock()
    res.scalars().all.return_value = instruments
    mock.execute.return_value = res
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_macro_events_endpoint(test_client):
    response = test_client.get("/macro/events")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert len(data["events"]) > 0


def test_macro_watchdog_endpoint(test_client):
    response = test_client.get("/macro/watchdog")
    assert response.status_code == 200
    data = response.json()
    assert "is_high_risk_window" in data


def test_market_universe_endpoint(test_client):
    response = test_client.get("/market/universe")
    assert response.status_code == 200
    data = response.json()
    assert data["total_instruments"] == 3
    assert "CRYPTO" in data["asset_classes"]
    assert "FX" in data["asset_classes"]
    assert "METAL" in data["asset_classes"]
