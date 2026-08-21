from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from apps.api.deps import get_redis_store, get_session
from apps.api.main import create_app


@pytest.fixture
def mock_redis_store():
    mock = MagicMock()
    mock.client = MagicMock()
    mock.client.ping = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_db_session():
    from swaram.models.instrument import Instrument
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
    inst_result = MagicMock()
    inst_result.scalars().first.return_value = inst

    runs_result = MagicMock()
    runs_result.scalars().all.return_value = []

    # Return different results per call
    mock.execute.side_effect = [inst_result, runs_result]
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_run_backtest_endpoint(test_client):
    payload = {
        "symbol": "BTCUSD",
        "start_time": "2026-08-21T00:00:00Z",
        "end_time": "2026-08-21T18:00:00Z",
        "initial_capital": 10000.0,
    }
    response = test_client.post("/backtest/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "sharpe_ratio" in data["metrics"]
    assert "max_drawdown" in data["metrics"]


def test_get_backtest_runs_endpoint(test_client):
    response = test_client.get("/backtest/runs")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
