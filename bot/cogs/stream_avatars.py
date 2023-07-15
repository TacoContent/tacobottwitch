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
        _method = inspect.stack()[0][3]
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]

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
          "action_message": r"^(?P<challenger>@?[a-zA-Z0-9-_]+) Has Challenged (?P<challenged>@?[a-zA-Z0-9-_]+) To A Duel with a buyin of \d{1,}. Type \!accept or \!decline within \d{1,} seconds$"
        }

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        _method = inspect.stack()[0][3]
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
                self.log.debug(channel, f"{self._module}.{_method}", "Event disabled")
                return
            pattern = game_settings.get("action_message", self.default_settings['action_message'])

            match_regex = re.compile(pattern, re.IGNORECASE| re.MULTILINE )

            if sender != channel:
                return

            # if message.content matches epic regex
            match = match_regex.match(message.content)
            if match:
                # get the user
                challenged = utils.clean_channel_name(match.group("challenged"))
                challenger = utils.clean_channel_name(match.group("challenger"))

                if challenged != utils.clean_channel_name(self.bot.nick):
                    self.log.debug(channel, f"{self._module}.{_method}", "Challenged is not the bot")
                    return
                # if the user is a known taco user, give tacos
                if not self.permissions_helper.has_linked_account(challenger):
                    await message.channel.send("!decline")
                    return

                else:
                    await message.channel.send("!accept")
                    return
            else:
                self.log.debug(channel, f"{self._module}.{_method}", "Message did not match regex")
                return

        except Exception as e:
            self.log.error(message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())
def prepare(bot) -> None:
    bot.add_cog(StreamAvatars(bot))
