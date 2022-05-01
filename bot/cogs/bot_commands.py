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

###
### The commands from this module are only called by the bot in restricted channels.
### They are triggered by twitch events that the bot receives in the users channels.
### The events are triggered via nodered.
###

class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.TACO_AMOUNT = 5

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "bot_commands.__init__", "Initialized")


    @commands.command(name="raid", aliases=["host"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def raid(self, ctx, source_channel: str, dest_channel: str) -> None:
        _method = inspect.stack()[1][3]
        try:
            source_channel = utils.clean_channel_name(source_channel)
            dest_channel = utils.clean_channel_name(dest_channel)

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT):
                # ONLY action if THIS account called the command
                return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"We are not in one of the restricted channels. we are in {ctx.message.channel.name}.")
                return

            # check the source channel is a channel that is a taco channel (this should never be false)
            if not self.permissions_helper.has_linked_account(source_channel):
                self.log.debug(ctx.message.channel.name, _method, f"Source channel {source_channel} is not a known taco user.")
                return
            # check if the destination channel is a channel that is a "taco" channel
            if not self.permissions_helper.has_linked_account(dest_channel):
                self.log.debug(ctx.message.channel.name, _method, f"Destination channel {dest_channel} is not a known taco user.")
                return

            reason = f"raiding the channel {dest_channel}"
            await self.tacos_log.give_user_tacos(ctx.message.channel.name, source_channel, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=self.TACO_AMOUNT)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    @commands.command(name="support")
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def support(self, ctx, username: str, channel: str) -> None:
        """
        Give a user tacos for supporting a channel.
        This can be subscribing, gifting, or cheer bits >= 100
        """
        _method = inspect.stack()[1][3]
        try:
            username = utils.clean_channel_name(username)
            channel = utils.clean_channel_name(channel)

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT):
                # ONLY action if THIS account called the command
                return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"We are not in one of the restricted channels. we are in {ctx.message.channel.name}.")
                return

            # check the source channel is a channel that is a taco channel (this should never be false)
            if not self.permissions_helper.has_linked_account(username):
                self.log.debug(ctx.message.channel.name, _method, f"Source channel {username} is not a known taco user.")
                return
            # check if the destination channel is a channel that is a "taco" channel
            if not self.permissions_helper.has_linked_account(channel):
                self.log.debug(ctx.message.channel.name, _method, f"Destination channel {channel} is not a known taco user.")
                return

            reason = f"supporting the channel {channel}"
            await self.tacos_log.give_user_tacos(ctx.message.channel.name, username, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=self.TACO_AMOUNT)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

def prepare(bot) -> None:
    bot.add_cog(BotCommands(bot))
