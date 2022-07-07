from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import logger
from .lib import loglevel


class TacoGameKeyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", "game_key.__init__", "Initialized")

    @commands.command(name="game")
    async def game(self, ctx) -> None:
        if ctx.message.echo:
            return
        channel = utils.clean_channel_name(ctx.message.channel.name)
        game = self.db.get_active_game_offer()
        if game:
            invite_data = self.db.get_invite_for_user(channel)
            if not invite_data:
                self.log.debug(channel, "game_key.game", "Looking for random invite")
                invite_data = self.db.get_any_invite()

            if invite_data:
                await ctx.send(
                    f"TACO Game Redeem: Get a key for '{game['title']}' using your tacos 🌮. -> {invite_data['info']['url']}"
                )
            else:
                self.log.debug(channel, "game_key.game", "No invite found. Just sending the game info.")
                await ctx.send(f"TACO Game Redeem: Get a key for '{game['title']}' using your tacos 🌮.")
        else:
            self.log.warn(channel, "game_key.game", "No game found.")
            await ctx.send(f"No TACO Game Redeem currently active. Check back later.")
def prepare(bot) -> None:
    bot.add_cog(TacoGameKeyCog(bot))
