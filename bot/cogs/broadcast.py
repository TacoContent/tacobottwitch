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

class TacoBroadcastCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()

        self.log.debug("NONE", "broadcast.__init__", "Initialized")

    @commands.command(name="broadcast")
    @commands.cooldown(1, 30, commands.Bucket.channel)
    async def broadcast(self, ctx) -> None:
        _method = inspect.stack()[1][3]

        try:
            if ctx.message.echo:
                return

            # Only the bot owner can send a broadcast to all channels.
            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT_OWNER):
                self.log.debug(ctx.message.channel.name, _method, f"{ctx.message.author.name} does not have permission to use this command.",)
                return

            

        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())
