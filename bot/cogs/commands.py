import twitchio
from twitchio.ext import commands
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

class Commands(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.commands_url = "https://tacocontent.github.io/ourtacobot/twitch"

    @commands.command(name="commands")
    @commands.cooldown(1, 30, commands.Bucket.channel)
    async def commands_list(self, ctx) -> None:
        await ctx.reply(f"View the available commands by going to {self.commands_url}")

def prepare(bot) -> None:
    bot.add_cog(Commands(bot))
