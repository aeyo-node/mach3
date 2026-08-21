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
    inst = Instrument(
        id=1,
        canonical_symbol="CRYPTO:BTC/USD",
        asset_class="crypto",
        base_asset="BTC",
        quote_asset="USD",
        venue="delta",
        provider_symbol="BTCUSD",
    )
    res = MagicMock()
    res.scalars().first.return_value = inst
    mock.execute.return_value = res
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_get_balances_endpoint(test_client):
    response = test_client.get("/account/balances")
    assert response.status_code == 200
    data = response.json()
    assert "balances" in data


def test_get_positions_endpoint(test_client):
    response = test_client.get("/account/positions")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data


def test_place_order_endpoint(test_client):
    payload = {
        "symbol": "BTCUSD",
        "side": "buy",
        "quantity": 10,
        "order_type": "market"
    }
    response = test_client.post("/order/place", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["order"]["symbol"] == "BTCUSD"
