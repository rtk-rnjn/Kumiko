import logging
import signal
from pathlib import Path as SyncPath
from typing import Dict, Optional

import asyncpg
import discord
from aiohttp import ClientSession
from Cogs import EXTENSIONS, VERSION
from discord.ext import commands, ipcx
from Libs.utils import ensure_postgres_conn, ensure_redis_conn, get_prefix
from Libs.utils.help import KumikoHelpPaginated
from lru import LRU
from redis.asyncio.connection import ConnectionPool

# Some weird import logic to ensure that watchfiles is there
_fsw = True
try:
    from watchfiles import awatch
except ImportError:
    _fsw = False


class KumikoCore(commands.Bot):
    """The core of Kumiko - Subclassed this time"""

    def __init__(
        self,
        intents: discord.Intents,
        config: Dict[str, Optional[str]],
        session: ClientSession,
        pool: asyncpg.Pool,
        redis_pool: ConnectionPool,
        ipc_secret_key: str,
        ipc_host: str,
        lru_size: int = 256,
        dev_mode: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(
            intents=intents,
            command_prefix=get_prefix,
            help_command=KumikoHelpPaginated(),
            activity=discord.Activity(type=discord.ActivityType.watching, name=">help"),
            *args,
            **kwargs,
        )
        self.dev_mode = dev_mode
        self.lru_size = lru_size
        self._config = config
        self._session = session
        self._ipc_secret_key = ipc_secret_key
        self._ipc_host = ipc_host
        self._pool = pool
        self._redis_pool = redis_pool
        self._prefixes: LRU = LRU(self.lru_size)
        self.default_prefix = ">"
        self.ipc = ipcx.Server(
            self, host=self._ipc_host, secret_key=self._ipc_secret_key
        )
        self.logger: logging.Logger = logging.getLogger()

    @property
    def config(self) -> Dict[str, Optional[str]]:
        """Global configuration dictionary read from .env files

        This is used to access API keys, and many others from the bot.

        Returns:
            Dict[str, Optional[str]]: A dictionary of configuration values
        """
        return self._config

    @property
    def session(self) -> ClientSession:
        """A global web session used throughout the lifetime of the bot

        Returns:
            ClientSession: AIOHTTP's ClientSession
        """
        return self._session

    @property
    def pool(self) -> asyncpg.Pool:
        """A global object managed throughout the lifetime of Kumiko

        Holds the asyncpg pool for connections

        Returns:
            asyncpg.Pool: asyncpg connection pool
        """
        return self._pool

    @property
    def redis_pool(self) -> ConnectionPool:
        """A global object managed throughout the lifetime of Kumiko

        Returns:
            ConnectionPool: Redis connection pool
        """
        return self._redis_pool

    @property
    def version(self) -> str:
        """The version of Kumiko

        Returns:
            str: The version of Kumiko
        """
        return str(VERSION)

    # It is preffered in this case to keep an LRU cache instead of a regular Dict cache
    # For example, if an running instance keeps 100 entries ({guild_id: prefix})
    # then this would take up too much memory.
    #
    # By instead using an LRU cache, if we reach the max, then we evict the prefix from the guild that hasn't used it in a while
    # The limit for the LRU cache is set to 100
    #
    # The primary goal of Kumiko is to keep the footprint of the RAM usage as low as possible
    # We don't need to have the bot consuming 250-300MB of RAM like when Prisma was used.
    @property
    def prefixes(self) -> LRU:
        """A LRU cache of the guild prefixes

        The LRU cache's implementation is built in C,
        so we natively can keep the performance the same as if it was a regular dict

        Returns:
            LRU: LRU cache of the guild prefixes
        """
        return self._prefixes

    async def fs_watcher(self) -> None:
        cogs_path = SyncPath(__file__).parent.joinpath("Cogs")
        async for changes in awatch(cogs_path):
            changes_list = list(changes)[0]
            if changes_list[0].modified == 2:
                reload_file = SyncPath(changes_list[1])
                self.logger.info(f"Reloading extension: {reload_file.name[:-3]}")
                await self.reload_extension(f"Cogs.{reload_file.name[:-3]}")

    # Need to override context for custom ones
    # for now, we can just use the default commands.Context
    # async def get_context(
    #     self, origin: Union[discord.Interaction, discord.Message], /, *, cls=KContext
    # ) -> KContext:
    #     return await super().get_context(origin, cls=cls)

    async def setup_hook(self) -> None:
        def stop():
            self.loop.create_task(self.close())

        self.loop.add_signal_handler(signal.SIGTERM, stop)
        self.loop.add_signal_handler(signal.SIGINT, stop)
        for cog in EXTENSIONS:
            self.logger.debug(f"Loaded extension: {cog}")
            await self.load_extension(cog)

        await self.ipc.start()

        self.loop.create_task(ensure_postgres_conn(self._pool))
        self.loop.create_task(ensure_redis_conn(self._redis_pool))

        if self.dev_mode is True and _fsw is True:
            self.logger.info("Dev mode is enabled. Loading Jishaku and FSWatcher")
            self.loop.create_task(self.fs_watcher())
            await self.load_extension("jishaku")

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()
        curr_user = None if self.user is None else self.user.name
        self.logger.info(f"{curr_user} is fully ready!")

    async def on_ipc_ready(self):
        self.logger.info(
            "Standard IPC Server started on %s:%s", self.ipc.host, self.ipc.port
        )
        self.logger.info(
            "Multicast IPC server started on %s:%s",
            self.ipc.host,
            self.ipc.multicast_port,
        )
