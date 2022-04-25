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

class FirstChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.TACO_AMOUNT = 1
        self.TIME_PERIOD = 86400 # 24 hours

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "first_chat.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        try:
            if message.author is None or message.channel is None:
                return
            if message.echo:
                return

            user = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)
            message = message.content
            is_first_message = self.db.track_user_message_in_chat(channel, user, message, self.TIME_PERIOD)
            if is_first_message:
                reason = f"their first message today in {channel}'s chat"
                await self.tacos_log.give_user_tacos(utils.clean_channel_name(self.settings.bot_name), user, reason, amount=self.TACO_AMOUNT)
        except Exception as e:
            self.log.error(message.channel.name, "first_chat.event_message", str(e), traceback.format_exc())

def prepare(bot):
    bot.add_cog(FirstChatCog(bot))
