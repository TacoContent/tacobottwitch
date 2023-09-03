###
### The commands from this module are only called by the bot in restricted channels.
### They are triggered by twitch events that the bot receives in the users channels.
### The events are triggered via nodered.
###
import os
import traceback
import inspect

from bot.cogs.lib import logger, loglevel, mongo, permissions, settings, tacos_log, tacotypes, utils
from twitchio.ext import commands


class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        # get the file name without the extension and without the directory
        self._class = self.__class__.__name__
        self._module = os.path.basename(__file__)[:-3]
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
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    @commands.command(name="raid", aliases=["host"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def raid(self, ctx, source_channel: str, dest_channel: str) -> None:
        _method = inspect.stack()[1][3]
        try:
            source_channel = utils.clean_channel_name(source_channel)
            dest_channel = utils.clean_channel_name(dest_channel)

            if not self._check_permission(ctx, f"{self._module}.{self._class}.{_method}", source_channel, dest_channel):
                return

            reason = f"raiding the channel {dest_channel}"
            await self.tacos_log.give_user_tacos(
                ctx.message.channel.name,
                source_channel,
                reason,
                give_type=tacotypes.TacoTypes.TWITCH_RAID,
                amount=self.TACO_AMOUNT,
            )
        except Exception as e:
            self.log.error(
                ctx.message.channel.name,
                f"{self._module}.{self._class}.{_method}",
                str(e),
                traceback.format_exc(),
            )

    @commands.command(name="subscribe")
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def subscribe(self, ctx, username: str, channel: str) -> None:
        """
        Give a user tacos for supporting a channel.
        This can be subscribing, gifting a sub, resubscribing... etc.
        """
        _method = inspect.stack()[1][3]
        try:
            username = utils.clean_channel_name(username)
            channel = utils.clean_channel_name(channel)

            if not self._check_permission(ctx, f"{self._module}.{self._class}.{_method}", username, channel):
                return

            reason = f"supporting the channel {channel} with a subscription"
            await self.tacos_log.give_user_tacos(
                ctx.message.channel.name,
                username,
                reason,
                give_type=tacotypes.TacoTypes.TWITCH_SUB,
                amount=25,
            )
        except Exception as e:
            self.log.error(
                ctx.message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )

    @commands.command(name="cheer")
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def cheer(self, ctx, username: str, channel: str) -> None:
        """
        Give a user tacos for supporting a channel with bits >= 100.
        """
        _method = inspect.stack()[1][3]
        try:
            username = utils.clean_channel_name(username)
            channel = utils.clean_channel_name(channel)

            if not self._check_permission(ctx, f"{self._module}.{self._class}.{_method}", username, channel):
                return

            reason = f"supporting the channel {channel} with bits"
            # maybe we should make this a percentage of the bits?
            await self.tacos_log.give_user_tacos(
                ctx.message.channel.name,
                username,
                reason,
                give_type=tacotypes.TacoTypes.TWITCH_BITS,
                amount=10,
            )
        except Exception as e:
            self.log.error(
                ctx.message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )

    @commands.command(name="follow")
    async def follow(self, ctx, username: str, channel: str) -> None:
        """
        Give a user tacos for following a channel.
        """
        _method = inspect.stack()[1][3]
        try:
            username = utils.clean_channel_name(username)
            channel = utils.clean_channel_name(channel)

            if not self._check_permission(ctx, f"{self._module}.{self._class}.{_method}", username, channel):
                return

            reason = f"supporting the channel {channel} with a follow"
            await self.tacos_log.give_user_tacos(
                ctx.message.channel.name, username, reason, give_type=tacotypes.TacoTypes.TWITCH_FOLLOW, amount=10
            )
        except Exception as e:
            self.log.error(
                ctx.message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )

    def _check_permission(self, ctx, source, username: str, channel: str) -> bool:
        username = utils.clean_channel_name(username)
        channel = utils.clean_channel_name(channel)
        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT):
            # ONLY action if THIS account called the command
            return False
        if not self.permissions_helper.in_command_restricted_channel(ctx):
            self.log.debug(
                ctx.message.channel.name,
                f"{source}",
                f"We are not in one of the restricted channels. we are in {ctx.message.channel.name}.",
            )
            return False

        # check the source channel is a channel that is a taco channel (this should never be false)
        if not self.permissions_helper.has_linked_account(username):
            self.log.debug(
                ctx.message.channel.name, f"{source}", f"Source channel {username} is not a known taco user."
            )
            return False
        # check if the destination channel is a channel that is a "taco" channel
        if not self.permissions_helper.has_linked_account(channel):
            self.log.debug(
                ctx.message.channel.name, f"{source}", f"Destination channel {channel} is not a known taco user."
            )
            return False
        return True


def prepare(bot) -> None:
    bot.add_cog(BotCommands(bot))
