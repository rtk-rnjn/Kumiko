import discord
from kumikocore import KumikoCore
from Libs.utils import CancelledActionEmbed, SuccessActionEmbed


class DeletePrefixView(discord.ui.View):
    def __init__(self, bot: KumikoCore, prefix: str) -> None:
        super().__init__()
        self.bot = bot
        self.prefix = prefix
        self.pool = self.bot.pool

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.green,
        emoji="<:greenTick:596576670815879169>",
    )
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        query = """
        UPDATE guild
        SET prefix = ARRAY_REMOVE(prefix, $1)
        WHERE id=$2;
        """
        async with self.pool.acquire() as conn:
            guild_id = interaction.guild.id  # type: ignore # lying again
            await conn.execute(query, self.prefix, guild_id)
            self.bot.prefixes[guild_id].remove(
                self.prefix
            )  # This makes the assumption that the guild is already in the LRU cache. This is not the best - Noelle
            self.clear_items()
            embed = SuccessActionEmbed(
                description=f"The prefix `{self.prefix}` was successfully removed"
            )
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.red,
        emoji="<:redTick:596576672149667840>",
    )
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.clear_items()
        embed = CancelledActionEmbed()
        await interaction.response.edit_message(embed=embed, view=self)