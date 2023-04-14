import os

import aiohttp
import ciso8601
import orjson
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt
from dotenv import load_dotenv
from Libs.errors import NotFoundError
from Libs.utils import Embed
from Libs.utils.pages import EmbedListSource, KumikoPages

load_dotenv()

GITHUB_API_KEY = os.environ["GITHUB_API_KEY"]


class Github(commands.Cog):
    """Search for releases and repos on GitHub"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(name="github")
    async def github(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # Force defaults to use Kumiko's repo ?
    @github.command(name="release-list")
    @app_commands.describe(owner="The owner of the repo", repo="The repo to search")
    async def githubReleasesList(
        self, ctx: commands.Context, owner: str, repo: str
    ) -> None:
        """Get up to 25 releases for a repo"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"token {GITHUB_API_KEY}",
                "accept": "application/vnd.github.v3+json",
            }
            params = {"per_page": 25}
            async with session.get(
                f"https://api.github.com/repos/{owner}/{repo}/releases",
                headers=headers,
                params=params,
            ) as r:
                data = await r.json(loads=orjson.loads)
                if r.status == 404:
                    raise NotFoundError
                else:
                    mainData = [
                        {
                            "title": item["name"],
                            "description": item["body"],
                            "thumbnail": item["author"]["avatar_url"],
                            "fields": [
                                {"name": "Author", "value": item["author"]["login"]},
                                {"name": "URL", "value": item["html_url"]},
                                {
                                    "name": "Created At",
                                    "value": format_dt(
                                        ciso8601.parse_datetime(item["created_at"])
                                    ),
                                },
                                {
                                    "name": "Published At",
                                    "value": format_dt(
                                        ciso8601.parse_datetime(item["published_at"])
                                    ),
                                },
                                {"name": "Tarball URL", "value": item["tarball_url"]},
                                {"name": "Zip URL", "value": item["zipball_url"]},
                                {
                                    "name": "Download URL",
                                    "value": [
                                        subItems["browser_download_url"]
                                        for subItems in item["assets"]
                                    ],
                                },
                                {
                                    "name": "Download Count",
                                    "value": str(
                                        [
                                            subItems["download_count"]
                                            for subItems in item["assets"]
                                        ]
                                    ).replace("'", ""),
                                },
                            ],
                        }
                        for item in data
                    ]
                    embedSource = EmbedListSource(mainData, per_page=1)
                    pages = KumikoPages(source=embedSource, ctx=ctx)
                    await pages.start()

    @github.command(name="repo")
    @app_commands.describe(owner="The owner of the repo", repo="The repo to search")
    async def searchGitHub(self, ctx: commands.Context, owner: str, repo: str) -> None:
        """Searches for one repo on GitHub"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"token {GITHUB_API_KEY}",
                "accept": "application/vnd.github.v3+json",
            }
            async with session.get(
                f"https://api.github.com/repos/{owner}/{repo}", headers=headers
            ) as r:
                data = await r.json(loads=orjson.loads)
                if r.status == 404:
                    raise NotFoundError
                else:
                    embed = Embed(title=data["name"], description=data["description"])
                    embed.set_thumbnail(url=data["owner"]["avatar_url"])
                    embed.add_field(name="Fork?", value=data["fork"])
                    embed.add_field(name="Private", value=data["private"])
                    embed.add_field(name="Stars", value=data["stargazers_count"])
                    embed.add_field(
                        name="Language",
                        value=data["language"]
                        if data["language"] is not None
                        else "None",
                    )
                    embed.add_field(name="URL", value=data["html_url"])
                    embed.add_field(
                        name="Homepage",
                        value=data["homepage"]
                        if data["homepage"] is not None
                        else "None",
                    )
                    embed.add_field(
                        name="Created At",
                        value=format_dt(ciso8601.parse_datetime(data["created_at"])),
                    )
                    embed.add_field(
                        name="Updated At",
                        value=format_dt(ciso8601.parse_datetime(data["updated_at"])),
                    )
                    embed.add_field(
                        name="Pushed At",
                        value=format_dt(ciso8601.parse_datetime(data["pushed_at"])),
                    )
                    await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Github(bot))