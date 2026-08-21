from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from apps.api.deps import get_redis_store, get_session
from apps.api.main import create_app


@pytest.fixture
def mock_redis_store():
    mock = MagicMock()
    mock.client = MagicMock()
    mock.client.ping = AsyncMock(return_value=True)
    mock.get_provider_health = AsyncMock(return_value={
        "connected": True,
        "last_message_at": "2026-08-21T18:00:00Z",
        "message_count": 500,
        "reconnect_count": 1,
        "error_count": 0
    })
    return mock


@pytest.fixture
def mock_db_session():
    mock = AsyncMock()
    res = MagicMock()
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


def test_telemetry_endpoint(test_client):
    response = test_client.get("/health/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "collectors" in data
    assert data["collectors"]["delta"]["active"] is True


def test_anomalies_endpoint(test_client):
    response = test_client.get("/market/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    assert len(data["anomalies"]) == 0
