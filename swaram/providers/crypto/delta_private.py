import hmac
import hashlib
import time
from typing import Any, Dict, Optional
import aiohttp
from swaram.core.logging import get_logger

logger = get_logger("providers.delta_private")


def generate_delta_signature(
    api_secret: str,
    method: str,
    timestamp: str,
    path: str,
    query_params: str = "",
    body: str = "",
) -> str:
    """Generate signature for Delta Exchange API request authentication."""
    message = f"{method.upper()}{timestamp}{path}{query_params}{body}"
    return hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


class DeltaPrivateRestClient:
    """Authorized Delta Exchange REST client for account state and order execution."""

    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_headers(self, method: str, path: str, query_params: str = "", body: str = "") -> Dict[str, str]:
        if not self.api_key or not self.api_secret:
            return {}

        timestamp = str(int(time.time()))
        signature = generate_delta_signature(
            api_secret=self.api_secret,
            method=method,
            timestamp=timestamp,
            path=path,
            query_params=query_params,
            body=body,
        )
        return {
            "api-key": self.api_key,
            "signature": signature,
            "timestamp": timestamp,
            "Content-Type": "application/json",
        }

    async def get_balances(self) -> Optional[Dict[str, Any]]:
        """Fetch asset balances and available margins."""
        path = "/v2/wallet/balances"
        url = f"{self.base_url}{path}"
        headers = self._get_headers("GET", path)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("result")
                    logger.warning(f"Failed to fetch balances", status=resp.status)
                    return None
        except Exception as e:
            logger.error("Error fetching balances from Delta", error=str(e))
            return None

    async def get_positions(self) -> Optional[Dict[str, Any]]:
        """Fetch active open derivative positions."""
        path = "/v2/positions"
        url = f"{self.base_url}{path}"
        headers = self._get_headers("GET", path)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("result")
                    return None
        except Exception as e:
            logger.error("Error fetching positions from Delta", error=str(e))
            return None

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Submit limit or market order to Delta Exchange."""
        path = "/v2/orders"
        url = f"{self.base_url}{path}"

        body_dict: Dict[str, Any] = {
            "symbol": symbol,
            "side": side.lower(),
            "size": int(quantity),
            "order_type": order_type.lower(),
        }
        if price is not None:
            body_dict["limit_price"] = str(price)

        import json
        body_str = json.dumps(body_dict)
        headers = self._get_headers("POST", path, body=body_str)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=body_str, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    data = await resp.json()
                    if resp.status in (200, 201):
                        return data.get("result")
                    logger.warning("Order placement failed", status=resp.status, response=data)
                    return None
        except Exception as e:
            logger.error("Error placing order on Delta", error=str(e))
            return None

    async def cancel_order(self, symbol: str, order_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a pending limit order on Delta Exchange."""
        path = "/v2/orders"
        url = f"{self.base_url}{path}"
        
        body_dict = {
            "symbol": symbol,
            "id": int(order_id),
        }
        import json
        body_str = json.dumps(body_dict)
        headers = self._get_headers("DELETE", path, body=body_str)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers, data=body_str, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        return data.get("result")
                    return None
        except Exception as e:
            logger.error("Error cancelling order on Delta", error=str(e))
            return None
