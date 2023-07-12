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

class RainmakerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 2
        self.bot_user = "rainmaker"

        self.event_name = "rainmaker"
        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]
        self.set_commands = ["set", "update"]

        self.default_settings = {
          "enabled": True,
          "action_message": r"^Thank you for tweeting out the stream, (?P<user>@?[a-zA-Z0-9-_]+).$"
        }

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

    @commands.command(name="rainmaker")
    async def rainmaker(self, ctx: commands.Context, subcommand: str = None, *args) -> None:
        _method = inspect.stack()[1][3]

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{_method}",
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        if subcommand is not None:
            if subcommand.lower() in self.stop_commands:
                await self._rainmaker_stop(ctx, args)
            elif subcommand.lower() in self.start_commands:
                await self._rainmaker_start(ctx, args)
            elif subcommand.lower() in self.set_commands:
                await self._rainmaker_set(ctx, args)

    async def _rainmaker_set(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        channel = utils.clean_channel_name(ctx.channel.name)
        try:

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BROADCASTER):
                self.log.debug(
                    channel,
                    f"{self._module}.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, f"{self._module}.{_method}", f"Stopping rainmaker event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if channel_settings is None:
                self.log.error(channel, f"{self._module}.{_method}", f"No rainmaker settings found for {channel}")
                return
            if args is None or len(args) == 0:
                self.log.error(channel, f"{self._module}.{_method}", f"No arguments provided for {channel}")
                return

            set_message = ' '.join(args[0:]).strip()
            channel_settings[self.bot_user]["action_message"] = set_message
            self.settings.set_channel_settings(self.db, channel, channel_settings)
            await ctx.reply(f"@{ctx.message.author.name} Your stream elements tip message has been set to '{set_message}'. Use {prefix}rainmaker set <regex> to change it.")
        except Exception as e:
            self.log.error(channel, f"{self._module}.{_method}", str(e), traceback.format_exc())

    async def _rainmaker_stop(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        try:
            channel = utils.clean_channel_name(ctx.channel.name)

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    f"{self._module}.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, f"{self._module}.{_method}", f"Stopping rainmaker event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings

            channel_settings[self.event_name]["enabled"] = False
            self.settings.set_channel_settings(self.db, channel, channel_settings)

            await ctx.reply(
                f"@{ctx.message.author.name}, I will no longer give tacos if someone that retweets and rainmaker notifies the channel. You can start it again with `{prefix}rainmaker start`."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{_method}", str(e), traceback.format_exc())

    async def _rainmaker_start(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        channel = utils.clean_channel_name(ctx.message.channel.name)
        try:

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    f"{self._module}.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, f"{self._module}.{_method}", f"Starting rainmaker event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings

            channel_settings[self.event_name]["enabled"] = True
            self.settings.set_channel_settings(self.db, channel, channel_settings)

            await ctx.reply(
                f"@{ctx.message.author.name}, I will now give tacos if someone that retweets the stream and rainmaker notifies the channel. You can stop it again with `{prefix}rainmaker stop`."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{_method}", str(e), traceback.format_exc())

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        _method = inspect.stack()[1][3]
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            game_settings = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                return

            rainmaker_regex = re.compile(game_settings.get("action_message", self.default_settings['action_message']), re.IGNORECASE | re.MULTILINE)

            if sender == channel:
                return

            # is the message from the bot?
            if sender == utils.clean_channel_name(self.bot_user):
                # if message.content matches epic regex
                match = rainmaker_regex.match(message.content)
                if match:
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            f"{self._module}.{_method}",
                            f"NON-TACO: {username} retweeted the stream in {channel}'s channel",
                        )
                        return

                    reason = f"retweeted the stream in {channel}'s channel"
                    self.log.debug(
                        channel,
                        f"{self._module}.{_method}",
                        f"{username} retweeted the stream in {channel}'s channel",
                    )
                    await self.tacos_log.give_user_tacos(
                        utils.clean_channel_name(self.settings.bot_name),
                        username,
                        reason,
                        give_type=tacotypes.TacoTypes.TWITCH_CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return

        except Exception as e:
            self.log.error(message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())
def prepare(bot) -> None:
    bot.add_cog(RainmakerCog(bot))
