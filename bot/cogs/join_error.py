# specific commands that are called only by the bot in the restricted channels.
import twitchio
from twitchio.ext import commands
import os
import traceback
import sys
import json
import inspect

from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import loglevel
from .lib import logger
from .lib import permissions
from .lib import command_helper
from .lib import tacos_log as tacos_log
from .lib import tacotypes

# Tracks a users first chat message in a channel in a 24 hour rolling window.
# give the user tacos for their first chat message in a channel.

class JoinErrorCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG


        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "join_error.__init__", "Initialized")

    @commands.Cog.event()
    async def event_channel_join_failure(self, channel) -> None:
        try:
            self.log.warn(channel, "join_error.event_channel_join_failure", f"Failed to join channel '{channel}'. Attempting Rejoin.", traceback.format_exc())
            await self.bot.join_channels([channel])
        except Exception as e:
            self.log.error(channel, "join_error.event_channel_join_failure", str(e), traceback.format_exc())

def prepare(bot) -> None:
    bot.add_cog(JoinErrorCog(bot))
