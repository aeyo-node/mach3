from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from swaram.storage.postgres import get_db_session
from swaram.storage.redis import RedisLiveStore, get_redis


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_db_session() as session:
        yield session


def get_redis_store() -> RedisLiveStore:
    return RedisLiveStore(get_redis())
