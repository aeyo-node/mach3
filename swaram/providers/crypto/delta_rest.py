from typing import Any, Dict, List, Optional
import aiohttp
from swaram.core.logging import get_logger

logger = get_logger("providers.delta_rest")


class DeltaRestClient:
    """Delta Exchange India Public REST client for instrument specifications and metadata."""

    def __init__(self, base_url: str = "https://cdn.india.delta.exchange"):
        self.base_url = base_url.rstrip("/")

    async def get_products(self) -> List[Dict[str, Any]]:
        """Fetch list of all active trading products and specifications."""
        url = f"{self.base_url}/v2/products"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("result", [])
                    else:
                        logger.warning("Failed to fetch Delta products", status=resp.status)
                        return []
        except Exception as e:
            logger.warning("Error calling Delta REST /v2/products", error=str(e))
            return []

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch latest REST snapshot for a symbol."""
        url = f"{self.base_url}/v2/tickers/{symbol}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("result")
                    return None
        except Exception as e:
            logger.warning(f"Error calling Delta REST /v2/tickers/{symbol}", error=str(e))
            return None

    async def get_candles(self, symbol: str, resolution: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch historical candles from Delta REST API."""
        url = f"{self.base_url}/v2/history/candles?symbol={symbol}&resolution={resolution}&limit={limit}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get("result", [])
                        if isinstance(res, list):
                            return res
                    logger.warning(f"Failed to fetch Delta candles for {symbol}", status=resp.status)
                    return []
        except Exception as e:
            logger.warning(f"Error fetching Delta candles for {symbol}", error=str(e))
            return []
