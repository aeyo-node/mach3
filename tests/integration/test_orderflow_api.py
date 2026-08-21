from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from apps.api.deps import get_redis_store, get_session
from apps.api.main import create_app
from swaram.models.instrument import Instrument
from swaram.models.market_data import OrderbookSnapshot


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
    
    ob = OrderbookSnapshot(
        timestamp=datetime.now(timezone.utc),
        instrument_id=1,
        provider="delta",
        depth=10,
        bids=[[65000.0, 10.0]],
        asks=[[65010.0, 10.0]],
    )

    inst_res = MagicMock()
    inst_res.scalars().first.return_value = inst

    ob_res = MagicMock()
    ob_res.scalars().first.return_value = ob

    def mock_execute(stmt, *args, **kwargs):
        stmt_str = str(stmt)
        if "instruments" in stmt_str:
            return inst_res
        return ob_res

    mock.execute.side_effect = mock_execute
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_orderflow_endpoint(test_client):
    response = test_client.get("/market/BTCUSD/orderflow")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_symbol"] == "CRYPTO:BTC/USD"
    assert "orderbook_analytics" in data
    assert "microprice" in data["orderbook_analytics"]


def test_positioning_endpoint(test_client):
    response = test_client.get("/market/BTCUSD/positioning")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_symbol"] == "CRYPTO:BTC/USD"
    assert "positioning_analytics" in data
    assert "funding_rate" in data["positioning_analytics"]
