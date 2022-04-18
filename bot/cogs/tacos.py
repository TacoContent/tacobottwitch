from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
from .lib import mongo
from .lib import settings
from .lib import logger
from .lib import loglevel


class TacosCog(commands.Cog):
    """Allows the streamer to give a user tacos"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.subcommands = ["give", "take", "balance", "leaderboard", "top", "stats", "help"]
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", "tacos.__init__", "Initialized")

    @commands.command(name="tacos")
    async def tacos(self, ctx, subcommand: str, *args):
        if subcommand in self.subcommands:
            if subcommand == "give":
                await self._tacos_give(ctx, args)
            elif subcommand == "take":
                await self._tacos_take(ctx, args)
            elif subcommand == "balance":
                await self._tacos_balance(ctx, args)
            elif subcommand == "leaderboard":
                await self._tacos_leaderboard(ctx, args)
            elif subcommand == "top":
                await self._tacos_top(ctx, args)
            elif subcommand == "stats":
                await self._tacos_stats(ctx, args)
            else:
                await self._tacos_help(ctx, args)
        else:
            await self._tacos_help(ctx, args)

    async def _tacos_give(self, ctx, args):
        if ctx.message.echo:
            return
        if len(args) >= 2:
            user = args[0]
            amount = args[1]
            reason = ""
            if len(args) > 2:
                reason = " ".join(args[2:])
            if amount.isdigit():
                amount = int(amount)
                if amount > 0:
                    taco_word = "taco"
                    if amount > 1:
                        taco_word = "tacos"
                    # if self.db.give_tacos(user, amount, reason):
                    await ctx.send(f"{user} has been given {amount} {taco_word} 🌮!")
                    # else:
                    #     await ctx.send(f"I do not know who {user} is in the discord.")
                else:
                    await ctx.send(f"You can't give negative tacos!")
            else:
                await ctx.send(f"{amount} is not a valid number!")
        else:
            await self._tacos_help(ctx, args)

    async def _tacos_help(self, ctx, args):
        if ctx.message.echo:
            return
        await ctx.send(f"Usage: !tacos give <user> <amount> [reason]")

    @commands.Cog.event()
    async def event_raw_data(self, data):
        pass

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        # is the message from the bot?
        if message.echo:
            return

        pass


def prepare(bot):
    bot.add_cog(TacosCog(bot))
