import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from swaram.config.settings import Settings, get_settings


@pytest.fixture
def mock_settings(monkeypatch):
    test_settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        delta_symbols=["BTCUSD", "ETHUSD"],
    )
    monkeypatch.setattr("swaram.config.settings.get_settings", lambda: test_settings)
    return test_settings
