from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import logger
from .lib import loglevel


class TacoQuestionOfTheDayCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", "toqtd.__init__", "Initialized")

    @commands.command(name="tqotd", aliases=["tqod"])
    async def tqotd(self, ctx) -> None:
        if ctx.message.echo:
            return
        channel = utils.clean_channel_name(ctx.message.channel.name)
        question = self.db.get_tqotd()
        if question:
            invite_data = self.db.get_invite_for_user(channel)
            if not invite_data:
                self.log.debug(channel, "tqotd.tqotd", "Looking for random invite")
                invite_data = self.db.get_any_invite()
            if invite_data:
                await ctx.send(
                    f"TACO Question of the Day: {question} -> Join the discussion: {invite_data['info']['url']}"
                )
            else:
                self.log.debug(channel, "tqotd.tqotd", "No invite found. Just sending the question.")
                await ctx.send(f"TACO Question of the Day: {question}")
        else:
            self.log.warn(channel, "tqotd.tqotd", "No question found.")
            await ctx.send(f"No TACO Question of the Day found. Check back later.")


def prepare(bot) -> None:
    bot.add_cog(TacoQuestionOfTheDayCog(bot))
