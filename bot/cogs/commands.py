import inspect
import os

from bot.cogs.lib import loglevel, logger, mongo, settings, tacos_log
from twitchio.ext import commands


class Commands(commands.Cog):
    def __init__(self, bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.commands_url = "https://tacocontent.github.io/ourtacobot/twitch"
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG
        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

    @commands.command(name="commands")
    @commands.cooldown(1, 30, commands.Bucket.channel)
    async def commands_list(self, ctx) -> None:
        await ctx.reply(f"View the available commands by going to {self.commands_url}")


def prepare(bot) -> None:
    bot.add_cog(Commands(bot))
