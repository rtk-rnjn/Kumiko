from __future__ import annotations

from typing import TYPE_CHECKING, Optional, TypedDict

import discord
from async_lru import alru_cache

if TYPE_CHECKING:
    from Bot.kumikocore import KumikoCore


class WebhookConfig(TypedDict):
    channel_id: int
    broadcast_url: str
    locked: bool


class WebhookDispatcher:
    def __init__(self, bot: KumikoCore, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.session = self.bot.session
        self.pool = self.bot.pool

    async def get_channel(self) -> Optional[discord.TextChannel]:
        conf = await self.get_webhook_config()
        if conf is None:
            return None
        guild = self.bot.get_guild(self.guild_id)
        return guild and guild.get_channel(conf["channel_id"])  # type: ignore

    async def get_webhook(self) -> Optional[discord.Webhook]:
        conf = await self.get_webhook_config()
        if conf is None:
            return None
        return discord.Webhook.from_url(url=conf["broadcast_url"], session=self.session)

    @alru_cache()
    async def get_webhook_config(self) -> Optional[WebhookConfig]:
        """Obtains the webhook configuration for a given guild

        This is used internally in order to fetch, and later send webhooks.
        """

        query = """
        SELECT channel_id, broadcast_url, locked
        FROM logging_webhooks
        WHERE id = $1;
        """
        rows = await self.pool.fetchrow(query, self.guild_id)
        if rows is None:
            return None

        config = WebhookConfig(**dict(rows))
        return config
