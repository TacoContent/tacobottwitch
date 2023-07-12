from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect
from .lib import mongo
from .lib import settings
from .lib import loglevel
from .lib import logger

class MessageLoggingCog(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        _method = inspect.stack()[0][3]
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self.bot = bot
        self.settings = settings.Settings()
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

    @commands.Cog.event()
    async def event_raw_data(self, data) -> None:
        _method = inspect.stack()[0][3]
        pass

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        _method = inspect.stack()[0][3]
        # is the message from the bot?
        if message.echo or message.author is None or message.channel is None:
            return

        print(f"{message.channel.name} -> {json.dumps(message.author.badges)} {message.author.name} -> {message.content}")

    @commands.Cog.event()
    async def event_ready(self) -> None:
        pass

def prepare(bot) -> None:
    bot.add_cog(MessageLoggingCog(bot))
