from unittest.mock import AsyncMock, patch
import pytest
from swaram.providers.crypto.delta_private import DeltaPrivateRestClient


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get")
async def test_get_balances(mock_get):
    # Mocking response
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"result": [{"asset": "USDT", "balance": "100.0"}]}
    mock_get.return_value.__aenter__.return_value = mock_resp

    client = DeltaPrivateRestClient("https://api.india.delta.exchange", "key", "secret")
    balances = await client.get_balances()

    assert balances is not None
    assert balances[0]["asset"] == "USDT"
    assert balances[0]["balance"] == "100.0"
