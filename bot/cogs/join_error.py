# specific commands that are called only by the bot in the restricted channels.
import inspect
import os
import traceback

from bot.cogs.lib import logger, loglevel, mongo, permissions, settings, tacos_log
from twitchio.ext import commands


class JoinErrorCog(commands.Cog):
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

        self.channel_attempts = {}

    @commands.Cog.event()
    async def event_ready(self) -> None:
        _method = inspect.stack()[0][3]
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Ready")

    @commands.Cog.event()
    async def event_channel_joined(self, channel) -> None:
        _method = inspect.stack()[0][3]
        self.log.debug(channel.name, f"{self._module}.{self._class}.{_method}", f"Joined channel '{channel.name}'")
        if channel.name in self.channel_attempts:
            del self.channel_attempts[channel.name]

    @commands.Cog.event()
    async def event_channel_join_failure(self, channel) -> None:
        _method = inspect.stack()[0][3]
        try:
            if channel in self.channel_attempts:
                self.channel_attempts[channel] += 1
            else:
                self.channel_attempts[channel] = 1

            if self.channel_attempts[channel] > 3:
                self.log.error(
                    channel,
                    f"{self._module}.{self._class}.{_method}",
                    f"Failed to join channel '{channel}' after 3 attempts. Giving up.",
                    traceback.format_exc(),
                )
                return

            # get the number of channel attempted joins, and sum of the total number of attempts across all channels.
            total_attempts = sum(self.channel_attempts.values())
            if total_attempts > 20:
                self.log.error(
                    channel,
                    f"{self._module}.{self._class}.{_method}",
                    f"Failed to join channel '{channel}' after 20 attempts. Giving up.",
                    traceback.format_exc(),
                )
                # exit the bot.
                raise SystemExit(1)

            self.log.warn(
                channel,
                f"{self._module}.{self._class}.{_method}",
                f"Failed to join channel '{channel}'. Attempting Rejoin.",
                traceback.format_exc(),
            )
            await self.bot.join_channels([channel])
        except Exception as e:
            self.log.error(channel, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())


def prepare(bot) -> None:
    bot.add_cog(JoinErrorCog(bot))
