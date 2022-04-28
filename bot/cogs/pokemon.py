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

# PokemonCommunityGameCog: TwitchLit A wild Cacturne appears TwitchLit Catch it using !pokecatch (winners revealed in 90s)


class PokemonCommunityGameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)

        self.pokemon_user = "pokemoncommunitygame"

        self.pokemon_regex = re.compile(
            r"A\swild\s(?P<pokemon>(?:\w\s?)+)\sappears\sTwitchLit\sCatch\sit\susing\s!pokecatch", re.MULTILINE | re.IGNORECASE
        )

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "pokemon.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)
            if sender == channel:
                return

            # is the message from the pokemon bot?
            if sender == utils.clean_channel_name(self.pokemon_user):
                # if message.content matches purchase regex
                match = self.pokemon_regex.match(message.content)
                if match:
                    ctx_channel = self.bot.get_channel(channel)
                    if ctx_channel:
                        await ctx_channel.send("!pokecatch")
                else:
                    self.log.warn(sender, "pokemon.event_message", f"No match -> {message.content}")
        except Exception as e:
            self.log.error(message.channel.name, "pokemon.event_message", str(e), traceback.format_exc())

def prepare(bot):
    bot.add_cog(PokemonCommunityGameCog(bot))
