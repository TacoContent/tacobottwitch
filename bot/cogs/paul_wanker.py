import re
from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect
import asyncio

from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import loglevel
from .lib import logger
from .lib import permissions
from .lib import command_helper
from .lib import tacos_log as tacos_log
from .lib import tacotypes

# paul_wanker: !drop

class PaulWankerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)

        self.bot_user = "paul_wanker"

        self.drop_regex = re.compile(
            r"!drop", re.MULTILINE | re.IGNORECASE
        )

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "paul_wanker.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)
            ctx_channel = self.bot.get_channel(channel)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            game_settings = channel_settings.get(self.bot_user, { "enabled": True })
            if not game_settings.get("enabled", True):
                return

            if sender == channel or not ctx_channel:
                return

            # is the message from the paul wanker bot?
            if sender == utils.clean_channel_name(self.bot_user):
                # if message.content matches drop regex
                match = self.drop_regex.match(message.content.replace("\u0001ACTION ", ""))
                if match:
                    await asyncio.sleep(.5)
                    await ctx_channel.send("!drop")
                    return
        except Exception as e:
            self.log.error(channel, "paul_wanker.event_message", str(e), traceback.format_exc())

def prepare(bot):
    bot.add_cog(PaulWankerCog(bot))
