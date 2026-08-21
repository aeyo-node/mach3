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
    mock.get_snapshot = AsyncMock(return_value={"last": 65000.0, "bid": 64995.0, "ask": 65005.0, "spread": 10.0})
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
    res.scalars().all.return_value = []
    mock.execute.return_value = res
    return mock


@pytest.fixture
def test_client(mock_redis_store, mock_db_session):
    app = create_app()
    app.dependency_overrides[get_redis_store] = lambda: mock_redis_store
    app.dependency_overrides[get_session] = lambda: mock_db_session
    client = TestClient(app)
    return client


def test_agent_tool_schema_endpoint(test_client):
    response = test_client.get("/agent/tools/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tools"] >= 4
    assert len(data["tools"]) >= 4


def test_agent_tool_execute_endpoint(test_client):
    payload = {
        "tool_name": "get_market_snapshot",
        "arguments": {"symbol": "BTCUSD"}
    }
    response = test_client.post("/agent/tools/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["tool_name"] == "get_market_snapshot"
    assert "result" in data


def test_agent_hermes_context_endpoint(test_client):
    response = test_client.get("/agent/context/BTCUSD")
    assert response.status_code == 200
    data = response.json()
    assert "prompt_context_text" in data
    assert "SWRAM MARKET INTELLIGENCE STATE" in data["prompt_context_text"]
