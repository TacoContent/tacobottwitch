# specific commands that are called only by the bot in the restricted channels.
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


class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "bot_commands.__init__", "Initialized")


    @commands.command(name="raid", aliases=["host"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def raid(self, ctx, source_channel: str, dest_channel: str):
        _method = inspect.stack()[1][3]
        try:
            if not ctx.message.echo:
                # ONLY action if THIS account called the command
                return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                return

            reason = f"raiding the channel {dest_channel}"
            # await self.tacos_log.give_user_tacos(ctx.message.channel.name, source_channel, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=amount)
            # self.db.add_twitch_event(source_channel, dest_channel)
            # await ctx.send(f"{source_channel} raided {dest_channel}.")
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())
def prepare(bot):
    bot.add_cog(BotCommands(bot))
