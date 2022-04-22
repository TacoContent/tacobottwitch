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
            source_channel = self.clean_channel_name(source_channel)
            dest_channel = self.clean_channel_name(dest_channel)

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT):
                # ONLY action if THIS account called the command
                return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"We are not in one of the restricted channels. we are in {ctx.message.channel.name}.")
                return

            # check the source channel is a channel that is a taco channel (this should never be false)
            if not self.db.is_taco_known_channel(source_channel):
                self.log.warn(ctx.message.channel.name, _method, f"Source channel {source_channel} is not a taco channel.")
                return
            # check if the destination channel is a channel that is a "taco" channel
            if not self.db.is_taco_known_channel(dest_channel):
                self.log.warn(ctx.message.channel.name, _method, f"Destination channel {dest_channel} is not a taco channel.")
                return

            reason = f"raiding the channel {dest_channel}"
            await self.tacos_log.give_user_tacos(ctx.message.channel.name, source_channel, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=5)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    @commands.command(name="support")
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def support(self, ctx, username: str, channel: str):
        _method = inspect.stack()[1][3]
        try:
            username = self.clean_channel_name(username)
            channel = self.clean_channel_name(channel)

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT):
                # ONLY action if THIS account called the command
                return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"We are not in one of the restricted channels. we are in {ctx.message.channel.name}.")
                return

            # check the source channel is a channel that is a taco channel (this should never be false)
            if not self.db.is_taco_known_channel(username):
                self.log.warn(ctx.message.channel.name, _method, f"Source channel {username} is not a taco channel.")
                return
            # check if the destination channel is a channel that is a "taco" channel
            if not self.db.is_taco_known_channel(channel):
                self.log.warn(ctx.message.channel.name, _method, f"Destination channel {channel} is not a taco channel.")
                return

            reason = f"supporting the channel {channel}"
            await self.tacos_log.give_user_tacos(ctx.message.channel.name, username, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=10)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    def clean_channel_name(self, channel: str):
        return channel.lower().strip().replace("#", "").replace("@", "")
def prepare(bot):
    bot.add_cog(BotCommands(bot))
