from typing import Optional, Union

import ormsgpack
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from .key_builder import CommandKeyBuilder


class KumikoCache:
    """Kumiko's custom caching library. Uses Redis as the backend."""

    def __init__(self, connection_pool: ConnectionPool) -> None:
        self.connection_pool = connection_pool

    async def setBasicCache(
        self,
        key: Optional[str] = CommandKeyBuilder(
            prefix="cache", namespace="kumiko", id=None, command=None
        ),
        value: Union[str, bytes] = None,
        ttl: Optional[int] = 30,
    ) -> None:
        """Sets the command cache on Redis
        Args:
            key (Optional[str], optional): Key to set on Redis. Defaults to `CommandKeyBuilder(prefix="cache", namespace="kumiko", user_id=None, command=None)`.
            value (Union[str, bytes, dict]): Value to set on Redis. Defaults to None.
            ttl (Optional[int], optional): TTL for the key-value pair. Defaults to 30.
        """
        conn: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        await conn.set(name=key, value=ormsgpack.packb(value), ex=ttl)
        await conn.close()

    async def getBasicCache(self, key: str) -> str:
        """Gets the command cache from Redis

        Args:
            key (str): Key to get from Redis
        """
        conn: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        res = ormsgpack.unpackb(await conn.get(key))
        await conn.close()
        return res

    async def cacheExists(self, key: str) -> bool:
        """Checks to make sure if the cache exists

        Args:
            key (str): Redis key to check

        Returns:
            bool: Whether the key exists or not
        """
        client: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        keyExists = await client.exists(key) >= 1
        await client.close()
        return True if keyExists else False
