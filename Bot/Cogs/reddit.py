from typing import Literal, Optional

import asyncpraw
import orjson
from discord import PartialEmoji, app_commands
from discord.ext import commands
from kumikocore import KumikoCore
from Libs.ui.reddit import (
    RedditEntry,
    RedditMemeEntry,
    RedditMemePages,
    RedditPages,
)
from Libs.utils import GuildContext, parse_subreddit
from yarl import URL


class Reddit(commands.Cog):
    """Search, and view posts and memes from Reddit"""

    def __init__(self, bot: KumikoCore) -> None:
        self.bot = bot
        self.session = self.bot.session
        self._REDDIT_ID = self.bot.config["REDDIT_ID"]
        self._REDDIT_SECRET = self.bot.config["REDDIT_SECRET"]

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji.from_str("<:reddit:314349923103670272>")

    @commands.hybrid_group(name="reddit")
    async def reddit(self, ctx: GuildContext) -> None:
        """Reddit search and utility commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @reddit.command(name="search")
    @app_commands.describe(
        search="The search query to use",
        subreddit="Which subreddit to use. Defaults to all.",
    )
    async def search(
        self, ctx: GuildContext, *, search: str, subreddit: Optional[str] = "all"
    ) -> None:
        """Searches for posts on Reddit"""
        await ctx.defer()
        reddit = asyncpraw.Reddit(
            client_id=self._REDDIT_ID,
            client_secret=self._REDDIT_SECRET,
            user_agent="Kumiko (by /u/No767)",
            requestor_kwargs={"session": self.bot.session},
        )
        sub = await reddit.subreddit(parse_subreddit(subreddit))
        sub_search = sub.search(search)
        converted = [
            RedditEntry(
                title=post.title,
                description=post.selftext,
                image_url=post.url,
                author=post.author,
                upvotes=post.score,
                nsfw=post.over_18,
                flair=post.link_flair_text,
                num_of_comments=post.num_comments,
                post_permalink=post.permalink,
                created_utc=post.created_utc,
            )
            async for post in sub_search
        ]
        pages = RedditPages(entries=converted, ctx=ctx)
        await pages.start()

    @reddit.command(name="feed")
    @app_commands.describe(
        subreddit="Subreddit to search", filter="Sort filters. Defaults to New"
    )
    async def feed(
        self,
        ctx: GuildContext,
        subreddit: str,
        filter: Optional[Literal["New", "Hot", "Rising"]] = "New",
    ) -> None:
        """Gets a feed of posts from a subreddit"""
        await ctx.defer()
        reddit = asyncpraw.Reddit(
            client_id=self._REDDIT_ID,
            client_secret=self._REDDIT_SECRET,
            user_agent="Kumiko (by /u/No767)",
            requestor_kwargs={"session": self.bot.session},
        )
        sub = await reddit.subreddit(parse_subreddit(subreddit))
        sub_gen = (
            sub.new(limit=10)
            if filter == "New"
            else sub.hot(limit=10)
            if filter == "Hot"
            else sub.rising(limit=10)
        )
        converted = [
            RedditEntry(
                title=post.title,
                description=post.selftext,
                image_url=post.url,
                author=post.author,
                upvotes=post.score,
                nsfw=post.over_18,
                flair=post.link_flair_text,
                num_of_comments=post.num_comments,
                post_permalink=post.permalink,
                created_utc=post.created_utc,
            )
            async for post in sub_gen
        ]
        pages = RedditPages(entries=converted, ctx=ctx)
        await pages.start()

    @reddit.command(name="memes")
    @app_commands.describe(
        subreddit="Subreddit to search",
        amount="Amount of memes to return. Defaults to 5",
    )
    async def search_memes(
        self, ctx: GuildContext, subreddit: str, amount: Optional[int] = 5
    ) -> None:
        """Searches for memes on Reddit"""
        url = (
            URL("https://meme-api.com/gimme") / parse_subreddit(subreddit) / str(amount)
        )
        async with self.bot.session.get(url) as r:
            data = await r.json(loads=orjson.loads)
            converted = [
                RedditMemeEntry(
                    title=item["title"],
                    url=item["url"],
                    author=item["author"],
                    subreddit=item["subreddit"],
                    ups=item["ups"],
                    nsfw=item["nsfw"],
                    spoiler=item["spoiler"],
                    reddit_url=item["postLink"],
                )
                for item in data["memes"]
            ]
            pages = RedditMemePages(entries=converted, ctx=ctx)
            await pages.start()


async def setup(bot: KumikoCore) -> None:
    await bot.add_cog(Reddit(bot))
