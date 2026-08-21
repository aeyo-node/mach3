import json
from typing import Any, Dict, List, Optional
import redis.asyncio as aioredis
from swaram.config.settings import get_settings
from swaram.core.logging import get_logger
from swaram.core.time import now_utc, iso_utc, iso_ist

logger = get_logger("storage.redis")

_redis: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed.")


class RedisLiveStore:
    """Manages low-latency live market snapshots and provider health state in Redis."""

    def __init__(self, client: Optional[aioredis.Redis] = None):
        self.client = client or get_redis()

    async def update_snapshot(self, canonical_symbol: str, data: Dict[str, Any]) -> None:
        """Update live market snapshot hash in Redis."""
        key = f"market:snapshot:{canonical_symbol}"
        # Serialize nested structures or timestamps to JSON strings
        payload = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                payload[k] = json.dumps(v)
            elif v is not None:
                payload[k] = str(v)
        payload["last_updated_at"] = iso_utc()
        payload["last_updated_at_ist"] = iso_ist()
        await self.client.hset(key, mapping=payload)

    async def get_snapshot(self, canonical_symbol: str) -> Dict[str, Any]:
        """Fetch live market snapshot hash from Redis."""
        key = f"market:snapshot:{canonical_symbol}"
        raw = await self.client.hgetall(key)
        if not raw:
            return {}
        result = {}
        for k, v in raw.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                # Try float/int conversion
                try:
                    if "." in v:
                        result[k] = float(v)
                    else:
                        result[k] = int(v)
                except ValueError:
                    result[k] = v
        return result

    async def update_provider_health(self, provider: str, health_dict: Dict[str, Any]) -> None:
        """Store provider health status."""
        key = f"health:provider:{provider.lower()}"
        payload = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in health_dict.items() if v is not None}
        await self.client.hset(key, mapping=payload)

    async def get_provider_health(self, provider: str) -> Dict[str, Any]:
        """Retrieve provider health status."""
        key = f"health:provider:{provider.lower()}"
        raw = await self.client.hgetall(key)
        if not raw:
            return {}
        result = {}
        for k, v in raw.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                if v.lower() == "true":
                    result[k] = True
                elif v.lower() == "false":
                    result[k] = False
                else:
                    try:
                        result[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        result[k] = v
        return result

    async def get_all_provider_health(self) -> List[Dict[str, Any]]:
        """Retrieve all active provider health statuses."""
        keys = await self.client.keys("health:provider:*")
        results = []
        for k in keys:
            prov = k.replace("health:provider:", "")
            h = await self.get_provider_health(prov)
            if h:
                results.append(h)
        return results

    async def publish_event(self, channel: str, event_data: Dict[str, Any]) -> None:
        """Publish normalized event to Redis channel/stream."""
        payload = json.dumps(event_data)
        await self.client.publish(channel, payload)
