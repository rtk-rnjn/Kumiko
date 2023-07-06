import itertools
from typing import Any, Dict, List, Optional, Union

import discord
from discord.ext import commands, menus
from Libs.utils.pages import KumikoPages

# class BotCategories(discord.ui.Select):
#     def __init__(self, cogs: List[commands.Cog]) -> None:
#         options = [
#             discord.SelectOption(label=cog.qualified_name or "No", description=cog.description)
#             for cog in cogs if cog.qualified_name not in ["DevTools", "ErrorHandler", "IPCServer"]
#         ]
#         super().__init__(placeholder="Select a category...", options=options)

#     async def callback(self, interaction: discord.Interaction):


class GroupHelpPageSource(menus.ListPageSource):
    def __init__(
        self,
        group: Union[commands.Group, commands.Cog],
        entries: List[commands.Command],
        *,
        prefix: str,
    ):
        super().__init__(entries=entries, per_page=6)
        self.group: Union[commands.Group, commands.Cog] = group
        self.prefix: str = prefix
        self.title: str = f"{self.group.qualified_name} Commands"
        self.description: str = self.group.description

    async def format_page(self, menu: KumikoPages, commands: List[commands.Command]):
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            colour=discord.Colour(0xA8B9CD),
        )

        for command in commands:
            signature = f"{command.qualified_name} {command.signature}"
            embed.add_field(
                name=signature,
                value=command.short_doc or "No help given...",
                inline=False,
            )

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(
                name=f"Page {menu.current_page + 1}/{maximum} ({len(self.entries)} commands)"
            )

        embed.set_footer(
            text=f'Use "{self.prefix}help command" for more info on a command.'
        )
        return embed


class HelpSelectMenu(discord.ui.Select["HelpMenu"]):
    def __init__(self, entries: dict[commands.Cog, List[commands.Command]], bot):
        super().__init__(
            placeholder="Select a category...",
            min_values=1,
            max_values=1,
            row=0,
        )
        self.cmds: dict[commands.Cog, List[commands.Command]] = entries
        self.bot = bot
        self.__fill_options()

    def __fill_options(self) -> None:
        self.add_option(
            label="Index",
            emoji="\N{WAVING HAND SIGN}",
            value="__index",
            description="The help page showing how to use the bot.",
        )
        for cog, cmds in self.cmds.items():
            if not cmds:
                continue
            description = cog.description.split("\n", 1)[0] or None
            emoji = getattr(cog, "display_emoji", None)
            self.add_option(
                label=cog.qualified_name,
                value=cog.qualified_name,
                description=description,
                emoji=emoji,
            )

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        value = self.values[0]
        if value == "__index":
            await self.view.rebind(FrontPageSource(), interaction)
        else:
            cog = self.bot.get_cog(value)
            if cog is None:
                await interaction.response.send_message(
                    "Somehow this category does not exist?", ephemeral=True
                )
                return

            commands = self.cmds[cog]
            if not commands:
                await interaction.response.send_message(
                    "This category has no commands for you", ephemeral=True
                )
                return

            source = GroupHelpPageSource(
                cog, commands, prefix=self.view.ctx.clean_prefix
            )
            await self.view.rebind(source, interaction)


class HelpMenu(KumikoPages):
    def __init__(self, source: menus.PageSource, ctx: commands.Context):
        super().__init__(source, ctx=ctx, compact=True)

    def add_categories(
        self, commands: Dict[commands.Cog, List[commands.Command]]
    ) -> None:
        self.clear_items()
        self.add_item(HelpSelectMenu(commands, self.ctx.bot))
        self.fill_items()

    async def rebind(
        self, source: menus.PageSource, interaction: discord.Interaction
    ) -> None:
        self.source = source
        self.current_page = 0

        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update_labels(0)
        await interaction.response.edit_message(**kwargs, view=self)


class FrontPageSource(menus.PageSource):
    def is_paginating(self) -> bool:
        # This forces the buttons to appear even in the front page
        return True

    def get_max_pages(self) -> Optional[int]:
        # There's only one actual page in the front page
        # However we need at least 2 to show all the buttons
        return 2

    async def get_page(self, page_number: int) -> Any:
        # The front page is a dummy
        self.index = page_number
        return self

    def format_page(self, menu: HelpMenu, page: Any):
        embed = discord.Embed(title="Bot Help", colour=discord.Colour(0xA8B9CD))
        embed.description = "help"
        # embed.description = inspect.cleandoc(
        #     f"""
        #     Hello! Welcome to the help page.

        #     Use "{menu.ctx.clean_prefix}help command" for more info on a command.
        #     Use "{menu.ctx.clean_prefix}help category" for more info on a category.
        #     Use the dropdown menu below to select a category.
        # """
        # )

        # embed.add_field(
        #     name='Support Server',
        #     value='For more help, consider joining the official server over at https://discord.gg/DWEaqMy',
        #     inline=False,
        # )

        # created_at = time.format_dt(menu.ctx.bot.user.created_at, 'F')
        # if self.index == 0:
        #     embed.add_field(
        #         name='Who are you?',
        #         value=(
        #             "I'm a bot made by Danny#0007. I'm the oldest running Discord bot! I've been running since "
        #             f'{created_at}. I have features such as moderation, tags, starboard, and more. You can get more '
        #             'information on my commands by using the dropdown below.\n\n'
        #             "I'm also open source. You can see my code on [GitHub](https://github.com/Rapptz/RoboDanny)!"
        #         ),
        #         inline=False,
        #     )
        # elif self.index == 1:
        #     entries = (
        #         ('<argument>', 'This means the argument is __**required**__.'),
        #         ('[argument]', 'This means the argument is __**optional**__.'),
        #         ('[A|B]', 'This means that it can be __**either A or B**__.'),
        #         (
        #             '[argument...]',
        #             'This means you can have multiple arguments.\n'
        #             'Now that you know the basics, it should be noted that...\n'
        #             '__**You do not type in the brackets!**__',
        #         ),
        #     )

        #     embed.add_field(name='How do I use this bot?', value='Reading the bot signature is pretty simple.')

        #     for name, value in entries:
        #         embed.add_field(name=name, value=value, inline=False)

        return embed


class KumikoHelpPaginated(commands.HelpCommand):
    context: commands.Context

    def __init__(self):
        super().__init__(
            command_attrs={
                "cooldown": commands.CooldownMapping.from_cooldown(
                    1, 3.0, commands.BucketType.member
                ),
                "help": "Shows help about the bot, a command, or a category",
            }
        )

    async def on_help_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandInvokeError):
            # Ignore missing permission errors
            if (
                isinstance(error.original, discord.HTTPException)
                and error.original.code == 50013
            ):
                return

            await ctx.send(str(error.original))

    def get_command_signature(self, command: commands.Command) -> str:
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if parent:
                fmt = f"{parent} {fmt}"
            alias = fmt
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature}"

    async def send_bot_help(self, mapping):
        bot = self.context.bot

        def key(command) -> str:
            cog = command.cog
            return cog.qualified_name if cog else "\U0010ffff"

        entries: list[commands.Command] = await self.filter_commands(
            bot.commands, sort=True, key=key
        )

        all_commands: dict[commands.Cog, List[commands.Command]] = {}
        for name, children in itertools.groupby(entries, key=key):
            if name == "\U0010ffff":
                continue

            cog = bot.get_cog(name)
            assert cog is not None
            all_commands[cog] = sorted(children, key=lambda c: c.qualified_name)

        menu = HelpMenu(FrontPageSource(), ctx=self.context)
        menu.add_categories(all_commands)
        await menu.start()

    async def send_cog_help(self, cog):
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        menu = HelpMenu(
            GroupHelpPageSource(cog, entries, prefix=self.context.clean_prefix),
            ctx=self.context,
        )
        await menu.start()

    def common_command_formatting(self, embed_like, command):
        embed_like.title = self.get_command_signature(command)
        if command.description:
            embed_like.description = f"{command.description}\n\n{command.help}"
        else:
            embed_like.description = command.help or "No help found..."

    async def send_command_help(self, command):
        # No pagination necessary for a single command.
        embed = discord.Embed(colour=discord.Colour(0xA8B9CD))
        self.common_command_formatting(embed, command)
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        subcommands = group.commands
        if len(subcommands) == 0:
            return await self.send_command_help(group)

        entries = await self.filter_commands(subcommands, sort=True)
        if len(entries) == 0:
            return await self.send_command_help(group)

        source = GroupHelpPageSource(group, entries, prefix=self.context.clean_prefix)
        self.common_command_formatting(source, group)
        menu = HelpMenu(source, ctx=self.context)
        await menu.start()

    # def __init__(self) -> None:
    #     super().__init__(
    #         command_attrs={
    #             "help": "The help command for the bot",
    #             "cooldown": commands.CooldownMapping.from_cooldown(
    #                 1, 3.0, commands.BucketType.user
    #             ),
    #             "aliases": ["commands"],
    #         }
    #     )

    # async def send(self, **kwargs) -> None:
    #     """a shortcut to sending to get_destination"""
    #     await self.get_destination().send(**kwargs)

    # async def help_embed(
    #     self, title: str, description: str, commands: List[commands.Command]
    # ) -> None:
    #     """The default help embed builder

    #     Mainly used so we don't repeat ourselves when building help embeds

    #     Args:
    #         title (str): The title of the embed. Usually the name of the cog, group, etc
    #         description (str): The description of the embed. Usually the desc of the cog or group
    #         commands (List[commands.Command]): List of commands
    #     """
    #     filteredCommands = await self.filter_commands(commands)
    #     fieldSource = [
    #         (self.get_command_signature(command), command.help or "No help found...")
    #         for command in filteredCommands
    #     ]
    #     sources = FieldPageSource(
    #         entries=fieldSource,
    #         per_page=5,
    #         inline=False,
    #         clear_description=False,
    #         title=title or "No",
    #         description=description or "No help found...",
    #     )
    #     pages = KumikoPages(source=sources, ctx=self.context)
    #     await pages.start()

    # async def send_bot_help(
    #     self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]
    # ) -> None:
    #     """Generates the help embed when the default help command is called

    #     Args:
    #         mapping (Mapping[Optional[commands.Cog], List[commands.Command]]): Mapping of cogs to commands
    #     """
    #     ctx = self.context
    #     embed = Embed(title=f"{ctx.me.display_name} Help")
    #     embed.set_thumbnail(url=ctx.me.display_avatar)
    #     embed.description = f"{ctx.me.display_name} is a multipurpose bot built with freedom and choice in mind."
    #     usable = 0

    #     for (
    #         cog,
    #         cmds,
    #     ) in mapping.items():  # iterating through our mapping of cog: commands
    #         if filtered_commands := await self.filter_commands(cmds):
    #             # if no commands are usable in this category, we don't want to display it
    #             amount_commands = len(filtered_commands)
    #             usable += amount_commands
    #             if cog:  # getting attributes dependent on if a cog exists or not
    #                 name = cog.qualified_name
    #                 description = cog.description or "No description"
    #             else:
    #                 name = "No"
    #                 description = "Commands with no category"

    #             embed.add_field(
    #                 name=f"{name} Category [{amount_commands}]", value=description
    #             )

    #     # embed.description = f"{len(ctx.commands)} commands | {usable} usable"

    #     await self.send(embed=embed)

    # async def send_command_help(self, command: commands.Command) -> None:
    #     """Triggers when a `<prefix>help <command>` is called

    #     Args:
    #         command (commands.Command): The command to get help for
    #     """
    #     signature = self.get_command_signature(
    #         command
    #     )  # get_command_signature gets the signature of a command in <required> [optional]
    #     embed = Embed(title=signature, description=command.help or "No help found...")

    #     if cog := command.cog:
    #         embed.add_field(name="Category", value=cog.qualified_name)

    #     can_run = "No"
    #     # command.can_run to test if the cog is usable
    #     with contextlib.suppress(commands.CommandError):
    #         if await command.can_run(self.context):
    #             can_run = "Yes"

    #     embed.add_field(name="Usable", value=can_run)

    #     if command._buckets and (
    #         cooldown := command._buckets._cooldown
    #     ):  # use of internals to get the cooldown of the command
    #         embed.add_field(
    #             name="Cooldown",
    #             value=f"{cooldown.rate} per {cooldown.per:.0f} seconds",
    #         )

    #     await self.send(embed=embed)

    # async def send_cog_help(self, cog: commands.Cog) -> None:
    #     """Send the help command when a `<prefix>help <cog>` is called

    #     Args:
    #         cog (commands.Cog): The cog requested
    #     """
    #     title = cog.qualified_name or "No"
    #     await self.help_embed(
    #         title=f"{title} Category",
    #         description=cog.description,
    #         commands=cog.get_commands(),
    #     )

    # async def send_group_help(self, group):
    #     """triggers when a `<prefix>help <group>` is called"""
    #     title = self.get_command_signature(group)
    #     await self.help_embed(
    #         title=title, description=group.help, commands=group.commands
    #     )
