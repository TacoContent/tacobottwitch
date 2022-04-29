import re
from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect
import asyncio

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

        self.bot_user = "pokemoncommunitygame"

        self.pokemon_regex = re.compile(
            r"(?:\u0001ACTION\s)?TwitchLit\sA\swild\s(?P<pokemon>(?:\w\s?)+)\sappears\sTwitchLit\sCatch\sit\susing\s!pokecatch", re.MULTILINE | re.IGNORECASE
        )

        self.no_trainer_regex = re.compile(
            r"\@ourtacobot\sYou\sdon\'t\shave\sa\strainer\spass\syet\s🤨\sEnter\s!pokestart", re.MULTILINE | re.IGNORECASE
        )

        self.no_ball = re.compile(
            r"\@ourtacobot\sYou don't own that ball. Check the extension to see your items", re.MULTILINE | re.IGNORECASE
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
            ctx_channel = self.bot.get_channel(channel)

            if sender == channel or not ctx_channel:
                return


            # is the message from the pokemon bot?
            if sender == utils.clean_channel_name(self.bot_user):
                strip_msg = message.content.replace("\u0001ACTION", "").strip()
                # if message.content matches purchase regex
                match = self.pokemon_regex.match(strip_msg)
                if match:
                    pokemon = match.group("pokemon")
                    self.log.warn(channel, "pokemon.event_message", f"{channel} attempt to catch {pokemon}")
                    await ctx_channel.send("!pokecatch")
                    return
                match = self.no_trainer_regex.match(strip_msg)
                if match:
                    self.log.warn(channel, "pokemon.event_message", "No trainer found, initiating pokestart")
                    await ctx_channel.send("!pokestart")
                    await asyncio.sleep(3)
                    await ctx_channel.send("!pokecatch")
                    return
                match = self.no_ball.match(strip_msg)
                if match:
                    self.log.warn(channel, "pokemon.event_message", "No ball found, initiating purchase ball")
                    await ctx_channel.send("!pokeshop pokeball 1")
                    await asyncio.sleep(3)
                    await ctx_channel.send("!pokecatch")
                    return
                self.log.warn(channel, "pokemon.event_message", f"unknown message: {strip_msg}")
        except Exception as e:
            self.log.error(channel, "pokemon.event_message", str(e), traceback.format_exc())

def prepare(bot):
    bot.add_cog(PokemonCommunityGameCog(bot))
