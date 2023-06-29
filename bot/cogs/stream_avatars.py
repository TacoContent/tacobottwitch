import re
from twitchio.ext import commands
import twitchio
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

class StreamAvatars(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 2
        self.event_name = "stream_avatars"
        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]
        self.set_commands = ["set", "update"]

        self.default_settings = {
          "enabled": True,
          "action_message": r"^(?P<user>@?[a-zA-Z0-9-_]) Has Challenged @OurTacoBot To A Duel with a buyin of \d{1,}. Type !accept or !decline within 30 seconds$"
        }

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "stream_avatars.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            game_settings = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                return

            match_regex = re.compile(game_settings.get("action_message", self.default_settings['action_message']), re.IGNORECASE | re.MULTILINE)

            if sender == channel:
                return

            # is the message from the bot?
            if sender == utils.clean_channel_name(channel):
                # if message.content matches epic regex
                match = match_regex.match(message.content)
                if match:
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        await message.channel.send("!decline")
                        return

                    else:
                        await message.channel.send("!accept")
                        return

        except Exception as e:
            self.log.error(message.channel.name, "rainmaker.event_message", str(e), traceback.format_exc())
def prepare(bot) -> None:
    bot.add_cog(StreamAvatars(bot))
