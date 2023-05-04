from discord.ext import commands
from discord.utils import format_dt
from kumikocore import KumikoCore
from Libs.economy import getUser
from Libs.ui.economy import RegisterView
from Libs.utils import Embed, parseDatetime
from prisma.models import User


class Economy(commands.Cog):
    """Earn, sell, and interact with Kumiko's economy!"""

    def __init__(self, bot: KumikoCore) -> None:
        self.bot = bot
        super().__init__()

    @commands.hybrid_group(name="marketplace")
    async def eco(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @eco.command(name="buy")
    async def marketplaceBuy(self, ctx: commands.Context) -> None:
        """Buy an item from the marketplace"""
        await ctx.send("Buy")

    @eco.command(name="inventory", aliases=["inv"])
    async def marketplaceInv(self, ctx: commands.Context) -> None:
        """View your marketplace inventory"""
        currUser = await User.prisma().find_first(
            where={"id": ctx.author.id}, include={"user_inv": True}
        )
        if currUser is None:
            await ctx.send(
                embed=Embed(
                    title="No account!",
                    description="You don't even have an account yet!",
                )
            )
        else:
            if len() == 0:  # type: ignore
                await ctx.send(
                    embed=Embed(
                        title="No items!",
                        description="You don't have any items in your inventory!",
                    )
                )
            else:
                await ctx.send(
                    embed=Embed(title="Inventory", description="Here are your items!")
                )

    @commands.hybrid_command(name="register")
    async def register(self, ctx: commands.Context) -> None:
        """Create an account for the economy"""
        view = RegisterView()
        embed = Embed(
            title="Register",
            description="Register for the economy! Before you do so, please make sure to follow the TOS. By registering, you are agreeing to use these services.",
        )
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="wallet")
    async def wallet(self, ctx: commands.Context) -> None:
        """Checks your wallet"""
        user = await getUser(
            id=ctx.author.id, includes={"user_inv": False, "marketplace": False}
        )  # type: ignore
        if user is None:
            await ctx.send(
                embed=Embed(
                    title="No Wallet", description="You don't have a wallet yet!"
                )
            )
        else:
            userDesc = f"**Rank**: {user['rank']}\n**Balance**: {user['petals']}\n**Date Joined**: {format_dt(parseDatetime(user['date_joined']))}"  # type: ignore
            embed = Embed(
                title=f"{ctx.author.name}'s Wallet",
                description=userDesc,
            )
            embed.set_footer(text=f"User ID: {user['id']}")  # type: ignore
            await ctx.send(embed=embed)


async def setup(bot: KumikoCore) -> None:
    await bot.add_cog(Economy(bot))
