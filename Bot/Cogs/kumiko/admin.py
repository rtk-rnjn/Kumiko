import asyncio
import os
import uuid
from datetime import datetime, timedelta

import discord
import uvloop
from admin_logs_utils import KumikoAdminLogsUtils
from dateutil import parser
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands, pages
from dotenv import load_dotenv
from kumiko_ui_components import ALPurgeDataView
from pytimeparse.timeparse import timeparse
from rin_exceptions import ItemNotFound

load_dotenv()

POSTGRES_PASSWORD = os.getenv("Postgres_Password")
POSTGRES_SERVER_IP = os.getenv("Postgres_Server_IP")
POSTGRES_USERNAME = os.getenv("Postgres_Username")
POSTGRES_PORT = os.getenv("Postgres_Port")
POSTGRES_AL_DATABASE = os.getenv("Postgres_Kumiko_Database")
AL_CONNECTION_URI = f"postgresql+asyncpg://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER_IP}:{POSTGRES_PORT}/{POSTGRES_AL_DATABASE}"

alUtils = KumikoAdminLogsUtils(AL_CONNECTION_URI)


class Admin(commands.Cog):
    """A set of administrative commands"""

    def __init__(self, bot):
        self.bot = bot

    admin = SlashCommandGroup("admin", "Admin commands")
    adminTimeout = admin.create_subgroup("timeout", "Timeouts commands")
    adminLogs = admin.create_subgroup("logs", "Access admin logs")

    @admin.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def banMembers(
        self,
        ctx,
        *,
        user: Option(discord.Member, "The user to ban"),
        reason: Option(str, "The reason for the ban"),
    ):
        """Bans the requested user"""
        await alUtils.addALRow(
            uuid=str(uuid.uuid4()),
            guild_id=ctx.guild.id,
            action_user_name=ctx.author.name,
            user_affected_name=user.name,
            type_of_action="ban",
            reason=reason,
            date_issued=datetime.utcnow().isoformat(),
            duration=999,
            datetime_duration=None,
        )
        await user.ban(delete_message_days=7, reason=reason)
        embed = discord.Embed(
            title=f"Banned {user.name}", color=discord.Color.from_rgb(255, 51, 51)
        )
        embed.description = (
            f"**Successfully banned {user.name}**\n\n**Reason:** {reason}"
        )
        await ctx.respond(embed=embed)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @admin.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unbanMembers(
        self,
        ctx,
        *,
        user: Option(discord.Member, "The user to unban"),
        reason: Option(str, "The reason for the unban"),
    ):
        """Un-bans the requested user"""
        await alUtils.addALRow(
            uuid=str(uuid.uuid4()),
            guild_id=ctx.guild.id,
            action_user_name=ctx.author.name,
            user_affected_name=user.name,
            type_of_action="unban",
            reason=reason,
            date_issued=datetime.utcnow().isoformat(),
            duration=999,
            datetime_duration=None,
        )
        await ctx.guild.unban(user=user, reason=reason)
        embed = discord.Embed(
            title=f"Unbanned {user.name}", color=discord.Color.from_rgb(178, 171, 255)
        )
        embed.description = (
            f"**Successfully unbanned {user.name}**\n\n**Reason:** {reason}"
        )
        await ctx.respond(embed=embed, ephemeral=True)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @admin.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kickUser(
        self,
        ctx,
        *,
        user: Option(discord.Member, "The user to kick out of the server"),
        reason: Option(str, "The reason for why"),
    ):
        """Kicks the requested user"""
        await alUtils.addALRow(
            uuid=str(uuid.uuid4()),
            guild_id=ctx.guild.id,
            action_user_name=ctx.author.name,
            user_affected_name=user.name,
            type_of_action="kick",
            reason=reason,
            date_issued=datetime.utcnow().isoformat(),
            duration=0,
            datetime_duration=None,
        )
        await user.kick(reason=reason)
        embed = discord.Embed(
            title=f"Kicked {user.name}", color=discord.Color.from_rgb(206, 255, 186)
        )
        embed.description = (
            f"**Successfully kicked {user.name}**\n\n**Reason:** {reason}"
        )
        await ctx.respond(embed=embed, ephemeral=True)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @adminTimeout.command(name="duration")
    @commands.has_permissions(moderate_members=True)
    async def timeoutDuration(
        self,
        ctx,
        *,
        user: Option(discord.Member, "The user to timeout"),
        duration: Option(str, "The duration of the timeout"),
        reason: Option(str, "The reason for the timeout", default=None),
    ):
        """Applies a timeout to the user for a specified amount of time"""
        try:
            parsedTime = timeparse(duration)
            timeoutDuration = timedelta(seconds=parsedTime)
            await alUtils.addALRow(
                uuid=str(uuid.uuid4()),
                guild_id=ctx.guild.id,
                action_user_name=ctx.author.name,
                user_affected_name=user.name,
                type_of_action="timeout",
                reason=reason,
                date_issued=datetime.utcnow().isoformat(),
                duration=timeoutDuration,
                datetime_duration=None,
            )
            await user.timeout_for(duration=timeoutDuration, reason=reason)
            embed = discord.Embed(
                title=f"Timeout applied for {user.name}",
                color=discord.Color.from_rgb(255, 255, 102),
            )
            embed.description = f"{user.name }has been successfully timed out for {timeoutDuration}\n\n**Reason:** {reason}"
            await ctx.respond(embed=embed, ephemeral=True)
        except TypeError:
            await ctx.respond(
                embed=discord.Embed(
                    description="It seems like you may have mistyped the amount of time for the timeout. Some examples that you can use are the following: `1h`, `1d`, `2 hours`, `5d`"
                )
            )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @adminTimeout.command(name="remove")
    @commands.has_permissions(moderate_members=True)
    async def removeTimeout(
        self,
        ctx,
        *,
        user: Option(discord.Member, "The user to remove the timeout from"),
        reason: Option(str, "The reason why the timeout should be removed"),
    ):
        """Removes the timeout from the user"""
        await alUtils.addALRow(
            uuid=str(uuid.uuid4()),
            guild_id=ctx.guild.id,
            action_user_name=ctx.author.name,
            user_affected_name=user.name,
            type_of_action="timeout-remove",
            reason=reason,
            date_issued=datetime.utcnow().isoformat(),
            duration=0,
            datetime_duration=None,
        )
        await user.remove_timeout(reason=reason)
        embed = discord.Embed(
            title=f"Timeout removed for {user.name}",
            color=discord.Color.from_rgb(255, 251, 194),
        )
        embed.description = f"Timeout for {user.name} has been successfully removed\n\n**Reason:** {reason}"
        await ctx.respond(embed=embed, ephemeral=True)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @adminLogs.command(name="view")
    @commands.has_permissions(moderate_members=True)
    async def viewLogs(
        self,
        ctx,
        *,
        type_of_action: Option(
            str,
            "The type of action to look up",
            choices=[
                "All",
                "Ban",
                "Unban",
                "Kick",
                "Timeout-Remove",
                "Timeout-Duration",
            ],
        ),
    ):
        """Allows admins to view admin logs"""
        typeOfAction = type_of_action.lower()
        res = await alUtils.selAction(
            type_of_action=typeOfAction, guild_id=ctx.guild.id
        )
        if typeOfAction in ["all", "All"]:
            res = await alUtils.selAllGuildRows(guild_id=ctx.guild.id)
        else:
            res = await alUtils.selAction(
                type_of_action=typeOfAction, guild_id=ctx.guild.id
            )
        try:
            if len(res) == 0 or res is None:
                raise ItemNotFound
            else:
                mainPages = pages.Paginator(
                    pages=[
                        discord.Embed(
                            title=f"{str(dict(mainItems)['type_of_action']).title()} - {dict(mainItems)['user_affected_name']}",
                            description=dict(mainItems)["reason"],
                        )
                        .add_field(
                            name="Issuer",
                            value=dict(mainItems)["action_user_name"],
                            inline=True,
                        )
                        .add_field(
                            name="Affected User",
                            value=dict(mainItems)["user_affected_name"],
                            inline=True,
                        )
                        .add_field(
                            name="Date Issued",
                            value=parser.isoparse(
                                dict(mainItems)["date_issued"]
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            inline=True,
                        )
                        .add_field(
                            name="Duration",
                            value=dict(mainItems)["duration"],
                            inline=True,
                        )
                        .add_field(
                            name="Date Duration",
                            value=dict(mainItems)["date_duration"],
                            inline=True,
                        )
                        for mainItems in res
                    ],
                    loop_pages=True,
                )
                await mainPages.respond(ctx.interaction, ephemeral=True)
        except ItemNotFound:
            embedErrorMessage = "Sorry, but it seems like we can't find anything within the category that you selected. Please try again"
            await ctx.respond(
                embed=discord.Embed(description=embedErrorMessage), ephemeral=True
            )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    @adminLogs.command(name="purge")
    @commands.has_permissions(moderate_members=True)
    async def purgeALData(self, ctx):
        """Purges all of the AL data for that guild (CAN'T BE UNDONE)"""
        embed = discord.Embed()
        embed.description = "Do you really wish to delete all of the AL data for this guild? This cannot be undone."
        await ctx.respond(
            embed=embed, view=ALPurgeDataView(AL_CONNECTION_URI), ephemeral=True
        )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def setup(bot):
    bot.add_cog(Admin(bot))