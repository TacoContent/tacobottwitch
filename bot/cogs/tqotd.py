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
    def __init__(self):
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", "toqtd.__init__", "Initialized")

    @commands.command(name="tqotd")
    async def tqotd(self, ctx):
        if ctx.message.echo:
            return
        question = self.db.get_tqotd()
        if question:
            invite_data = self.db.get_invite_for_user(ctx.message.channel.name)
            if invite_data:
                await ctx.send(
                    f"TACO Question of the Day: {question} -> Join the discussion: {invite_data['info']['url']}"
                )
            else:
                await ctx.send(f"TACO Question of the Day: {question}")
        else:
            await ctx.send(f"No TACO Question of the Day found. Check back later.")


def prepare(bot):
    bot.add_cog(TacoQuestionOfTheDayCog())
