from typing import Any, Dict, Optional, Union

import redis.asyncio as redis
from Libs.utils import encodeDatetime
from redis.asyncio.connection import ConnectionPool

from .key_builder import CommandKeyBuilder


class KumikoCache:
    """Kumiko's custom caching library. Uses Redis as the backend."""

    def __init__(self, connection_pool: ConnectionPool) -> None:
        self.connection_pool = connection_pool

    async def setBasicCache(
        self,
        key: Optional[str],
        value: Union[str, bytes] = "",
        ttl: Optional[int] = 30,
    ) -> None:
        """Sets the command cache on Redis
        Args:
            key (Optional[str], optional): Key to set on Redis. Defaults to `CommandKeyBuilder(prefix="cache", namespace="kumiko", user_id=None, command=None)`.
            value (Union[str, bytes, dict]): Value to set on Redis. Defaults to None.
            ttl (Optional[int], optional): TTL for the key-value pair. Defaults to 30.
        """
        defaultKey = CommandKeyBuilder(
            prefix="cache", namespace="kumiko", id=None, command=None
        )
        conn: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        await conn.set(name=key if key is not None else defaultKey, value=value, ex=ttl)

    async def getBasicCache(self, key: str) -> Union[str, None]:
        """Gets the command cache from Redis

        Args:
            key (str): Key to get from Redis
        """
        conn: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        return await conn.get(key)

    async def setJSONCache(
        self,
        key: str,
        value: Union[Dict[str, Any], Any],
        path: str = "$",
        ttl: Union[int, None] = 5,
    ) -> None:
        """Sets the JSON cache on Redis

        Args:
            key (str): The key to use for Redis
            value (Union[Dict[str, Any], Any]): The value of the key-pair value
            path (str): The path to look for or set. Defautls to "$"
            ttl (Union[int, None], optional): TTL of the key-value pair. If None, then the TTL will not be set. Defaults to 5.
        """
        client: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        await client.json().set(
            name=key,
            path=path,
            obj=encodeDatetime(value) if isinstance(value, dict) else value,
        )
        if isinstance(ttl, int):
            await client.expire(name=key, time=ttl)

    # The output type comes from here: https://github.com/redis/redis-py/blob/9f503578d1ffed20d63e8023bcd8a7dccd15ecc5/redis/commands/json/_util.py#L3C1-L3C73
    async def getJSONCache(self, key: str) -> Union[None, Dict[str, Any]]:
        """Gets the JSON cache on Redis

        Args:
            key (str): The key of the key-value pair to get

        Returns:
            Dict[str, Any]: The value of the key-value pair
        """
        client: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        value = await client.json().get(name=key)
        return None if value is None else value

    async def deleteJSONCache(self, key: str, path: str = "$") -> None:
        """Deletes the JSON cache at key `key` and under `path`

        Args:
            key (str): The key to use in Redis
            path (str): The path to look for. Defaults to "$" (root)
        """
        client: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        await client.json().delete(key=key, path=path)

    async def cacheExists(self, key: str) -> bool:
        """Checks to make sure if the cache exists

        Args:
            key (str): Redis key to check

        Returns:
            bool: Whether the key exists or not
        """
        client: redis.Redis = redis.Redis(connection_pool=self.connection_pool)
        keyExists = await client.exists(key) >= 1
        return bool(keyExists)
