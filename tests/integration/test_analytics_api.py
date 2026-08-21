from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from apps.api.deps import get_redis_store, get_session
from apps.api.main import create_app
from swaram.models.instrument import Instrument
from swaram.models.market_data import Candle


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
    
    # Mock instrument query result
    inst_res = MagicMock()
    inst_res.scalars().first.return_value = inst
    
    # Mock candles query result
    now = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
    mock_candles = [
        Candle(
            timestamp=now,
            instrument_id=1,
            provider="delta",
            timeframe="1m",
            open=65000.0 + i,
            high=65100.0 + i,
            low=64950.0 + i,
            close=65050.0 + i,
            volume=10.0,
            trade_count=5,
        )
        for i in range(20)
    ]
    candle_res = MagicMock()
    candle_res.scalars().all.return_value = mock_candles

    def mock_execute(stmt, *args, **kwargs):
        stmt_str = str(stmt)
        if "instruments" in stmt_str:
            return inst_res
        return candle_res

    mock.execute.side_effect = mock_execute
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_get_indicators_endpoint(test_client):
    response = test_client.get("/market/BTCUSD/indicators")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_symbol"] == "CRYPTO:BTC/USD"
    assert "indicators" in data
    assert "rsi" in data["indicators"]
    assert "macd" in data["indicators"]


def test_get_structure_endpoint(test_client):
    response = test_client.get("/market/BTCUSD/structure")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_symbol"] == "CRYPTO:BTC/USD"
    assert "market_structure" in data
    assert "trend" in data["market_structure"]
