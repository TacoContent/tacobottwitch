# specific commands that are called only by the bot in the restricted channels.
import inspect
import os

from bot.cogs.lib import logger, loglevel, mongo, permissions, settings, tacos_log
from twitchio.ext import commands, eventsub


# https://twitchio.dev/en/latest/exts/eventsub.html
class EventSubCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()

        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    async def __ainit__(self) -> None:
        _method = inspect.stack()[0][3]
        # get all the channels that we are monitoring and create the eventsub subscriptions
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    @commands.Cog.event()
    async def event_eventsub_notification_followV2(self, payload: eventsub.ChannelFollowData) -> None:
        return None


def prepare(bot) -> None:
    bot.add_cog(EventSubCog(bot))
