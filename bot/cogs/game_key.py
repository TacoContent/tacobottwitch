import os
import inspect

from bot.cogs.lib import logger, loglevel, mongo, settings, utils
from twitchio.ext import commands


class TacoGameKeyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    @commands.command(name="game")
    async def game(self, ctx) -> None:
        _method = inspect.stack()[0][3]
        if ctx.message.echo:
            return
        channel = utils.clean_channel_name(ctx.message.channel.name)
        game = self.db.get_active_game_offer()
        if game:
            invite_data = self.db.get_invite_for_user(channel)
            if not invite_data:
                self.log.debug(channel, f"{self._module}.{self._class}.{_method}", "Looking for random invite")
                invite_data = self.db.get_any_invite()

            if invite_data:
                await ctx.send(
                    f"TACO Game Redeem: Get a key for '{game['title']}' using your tacos 🌮. -> {invite_data['info']['url']}"
                )
            else:
                self.log.debug(
                    channel, f"{self._module}.{self._class}.{_method}", "No invite found. Just sending the game info."
                )
                await ctx.send(f"TACO Game Redeem: Get a key for '{game['title']}' using your tacos 🌮.")
        else:
            self.log.warn(channel, f"{self._module}.{self._class}.{_method}", "No game found.")
            await ctx.send(f"No TACO Game Redeem currently active. Check back later.")


def prepare(bot) -> None:
    bot.add_cog(TacoGameKeyCog(bot))
