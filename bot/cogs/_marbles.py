import re
from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect
import asyncio
import math

from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import loglevel
from .lib import logger
from .lib import permissions
from .lib import command_helper
from .lib import tacos_log as tacos_log
from .lib import tacotypes


class MarblesOnStreamCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.game_name = "marblesonstream"

        self.subcommands = ["start", "on", "enable", "stop", "off", "disable"]

        self.marbles_start = re.compile(
            r"^!play(?:\s\d{1,})?$",
            re.MULTILINE | re.IGNORECASE,
        )
        self.game_title = re.compile(r"^marbles\son\sstream", re.MULTILINE | re.IGNORECASE)

        # try and get the suggested ball to use. then check if we have that ball. if not, try to buy it. if not successful, use a regular pokeball

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "pokemon.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)
            ctx_channel = self.bot.get_channel(channel)

            # check if we care about this message...
            match = self.marbles_start.match(message.content)
            if not match:
                return

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            game_settings = channel_settings.get(self.game_name, None)
            if game_settings is None:
                game_settings = {
                    "enabled": True,
                }
                channel_settings[self.game_name] = game_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            if not game_settings.get("enabled", True):
                # game is disabled. ignore this message
                return

            channel_info = await self.bot.fetch_channel(channel)
            if channel_info is None:
                self.log.debug(channel, "marbles.event_message", "Channel Info not found")
                return

            if not ctx_channel:
                return

            match = self.game_title.match(channel_info.game_name)
            if not match:
                self.log.debug(channel, "marbles.event_message", f"Not a marbles on stream game: {channel_info.game_name}")
                return

            # we are in a marbles on stream game.
            # and someone said "!play"

            # we need to see if we already entered...

            # await asyncio.sleep(1)
            # await ctx_channel.send("!play")
        except Exception as e:
            self.log.error(channel, "marbles.event_message", str(e), traceback.format_exc())


def prepare(bot) -> None:
    bot.add_cog(MarblesOnStreamCog(bot))
