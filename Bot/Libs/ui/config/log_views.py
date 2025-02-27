from __future__ import annotations

from typing import TYPE_CHECKING

import asyncpg
import discord
from discord.ext import commands
from Libs.config.cache import GuildCacheHandler, LoggingGuildConfig
from Libs.utils import KumikoView, WebhookDispatcher

from .utils import determine_status, format_desc

if TYPE_CHECKING:
    from Bot.Cogs.config import Config
    from Bot.kumikocore import KumikoCore


class LoggingConfigMenu(discord.ui.Select):
    def __init__(self, cog: Config, ctx: commands.Context) -> None:
        options = [
            discord.SelectOption(
                emoji=discord.PartialEmoji.from_str("<:blobban:759935431847968788>"),
                label="Moderation",
                description="Enabled/Disable Moderation Logs",
                value="mod",
            ),
            discord.SelectOption(
                emoji=discord.PartialEmoji.from_str(
                    "<:upward_stonks:739614245997641740>"
                ),
                label="Economy",
                description="Enable/Disable Local Economy Logs",
                value="eco",
            ),
            discord.SelectOption(
                emoji=discord.PartialEmoji(name="\U0001f500"),
                label="Redirects",
                description="Enable/Disable Redirects Logs",
                value="redirects",
            ),
        ]
        super().__init__(placeholder="Select a category...", options=options, row=0)
        self.cog = cog
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        value = self.values[0]
        current_status = self.cog.reserved_lgc[interaction.guild.id][value]
        view = LGCToggleView(self.cog, self.ctx, value)
        desc = format_desc(value, current_status)
        await interaction.response.send_message(desc, view=view)

        # So in this case, we just assign a runtime attr instead
        # Pyright does not like it
        view.original_response = await interaction.original_response()  # type: ignore


class LGCView(KumikoView):
    def __init__(self, bot: KumikoCore, cog: Config, ctx: commands.Context) -> None:
        super().__init__(ctx)
        self.conf_cog = cog
        self.bot = bot
        self.pool = self.bot.pool
        self.redis_pool = self.bot.redis_pool
        self.add_item(LoggingConfigMenu(cog, ctx))

    @discord.ui.button(label="Save and Finish", style=discord.ButtonStyle.green, row=1)
    async def save_and_finish(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        value_map = {"mod": "Moderation", "eco": "Economy", "redirects": "Redirects"}
        query = """
        UPDATE logging_config
        SET mod = $2,
            eco = $3,
            redirects = $4
        WHERE guild_id = $1;
        """
        if interaction.guild is None:
            return

        guild_id = interaction.guild.id
        cache = GuildCacheHandler(guild_id, self.redis_pool)
        cached_status = self.conf_cog.reserved_lgc.get(guild_id)
        if cached_status is None:
            return

        change_desc = "\n".join(
            [f"{value_map[k]}: {v}" for k, v in cached_status.items()]
        )
        desc = f"The following changes were made:\n{change_desc}"
        new_conf = LoggingGuildConfig(**cached_status)
        status_values = [v for v in cached_status.values()]
        await self.pool.execute(query, guild_id, *status_values)
        await cache.replace_config(".logging_config", new_conf)

        if guild_id in self.conf_cog.reserved_lgc:
            self.conf_cog.reserved_lgc.pop(guild_id)

        await interaction.response.defer()
        await interaction.edit_original_response(content=desc, embed=None, view=None)
        self.stop()


class LGCToggleView(KumikoView):
    def __init__(self, cog: Config, ctx: commands.Context, value: str) -> None:
        super().__init__(ctx)
        self.ctx = ctx
        self.conf_cog = cog
        self.value = value

    async def set_status(
        self,
        interaction: discord.Interaction,
        original_resp: discord.InteractionMessage,
        status: bool,
    ):
        str_status = determine_status(status)
        if interaction.guild is None or self.conf_cog is None:
            return

        guild_id = interaction.guild.id
        is_already_enabled = self.conf_cog.is_lgc_already_enabled(
            interaction.guild.id, self.value
        )
        if is_already_enabled is status:
            await interaction.response.send_message(
                f"Module `{self.value} is already {str_status.lower()}!`",
                ephemeral=True,
            )
            return

        if guild_id in self.conf_cog.reserved_lgc:
            self.conf_cog.reserved_lgc[guild_id][self.value] = status
            await original_resp.edit(content=format_desc(self.value, status))
            await interaction.response.send_message(
                f"Module `{self.value}` is now {str_status.lower()}", ephemeral=True
            )
            return

        await interaction.response.send_message("You did not start the config progress")

    @discord.ui.button(
        label="Enable",
        style=discord.ButtonStyle.green,
        emoji="<:greenTick:596576670815879169>",
        row=0,
    )
    async def enable(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.set_status(interaction, self.original_response, True)  # type: ignore

    @discord.ui.button(
        label="Disable",
        style=discord.ButtonStyle.red,
        emoji="<:redTick:596576672149667840>",
        row=0,
    )
    async def disable(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self.set_status(interaction, self.original_response, False)  # type: ignore

    @discord.ui.button(
        label="Finish",
        style=discord.ButtonStyle.grey,
    )
    async def finish(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()


class PurgeLGConfirmation(KumikoView):
    def __init__(
        self,
        bot: KumikoCore,
        ctx: commands.Context[KumikoCore],
        guild_id: int,
        pool: asyncpg.Pool,
    ) -> None:
        super().__init__(ctx)
        self.guild_id = guild_id
        self.dispatcher = WebhookDispatcher(bot, self.guild_id)
        self.pool = pool

    async def on_timeout(self) -> None:
        if self.message:  # type: ignore
            self.message.delete()  # type: ignore

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.green,
        emoji="<:greenTick:596576670815879169>",
        row=0,
    )
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        delete_query = "DELETE FROM logging_webhooks WHERE id = $1;"
        logging_channel = await self.dispatcher.get_channel()

        if logging_channel is None:
            await interaction.response.send_message(
                "Apparently you don't have a channel to begin with... Please run `config logs setup` to make one.",
                ephemeral=True,
            )
            return

        requested_user = interaction.user
        reason = f"{requested_user.name} (ID: {requested_user.id}) has requested to delete the logging chanel {logging_channel.name}"

        try:
            await logging_channel.delete(reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                "\N{NO ENTRY SIGN} I do not have permissions to delete channels and/or webhooks."
            )
            return
        except discord.HTTPException:
            await interaction.response.send_message(
                "\N{NO ENTRY SIGN} Unknown error happened"
            )
            return

        # Invalidate the cache so we can safely delete it
        self.dispatcher.get_webhook_config.cache_invalidate()
        await self.pool.execute(delete_query, self.guild_id)

        await self.message.edit(content="Logging channels have been successfully deleted", embed=None, view=None, delete_after=15.0)  # type: ignore
        self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.red,
        emoji="<:redTick:596576672149667840>",
        row=0,
    )
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()
