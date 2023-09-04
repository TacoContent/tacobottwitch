import inspect
import os
import re
import traceback
import typing

import twitchio
from bot.cogs.lib import logger, loglevel, mongo, permissions, settings, tacos_log, tacotypes, utils
from twitchio.ext import commands


# streamelements: inmax_cz just tipped $10.00 PogChamp
class StreamElementsBotCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 5

        self.event_name = "streamelements"

        self.default_settings = {
            "enabled": True,
            "tip_message": r"^(?P<user>\w+)\s(?:just\s)?tipped\s(?P<tip>[¥$₡£¢]?\d{1,}(?:\.\d{1,})?)",
        }

        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]
        self.tip_commands = ["tip"]

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    @commands.command(name="streamelements")
    async def streamelements(self, ctx: commands.Context, subcommand: typing.Optional[str] = None, *args) -> None:
        _method = inspect.stack()[1][3]

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{self._class}.{_method}",
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        if subcommand is not None:
            if subcommand.lower() in self.stop_commands:
                await self._streamelements_stop(ctx, args)
            elif subcommand.lower() in self.start_commands:
                await self._streamelements_start(ctx, args)
            elif subcommand.lower() in self.tip_commands:
                await self._streamelements_tip(ctx, args)

    async def _streamelements_tip(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        channel = utils.clean_channel_name(ctx.channel.name)
        try:
            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BROADCASTER):
                self.log.debug(
                    channel,
                    f"{self._module}.{self._class}.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(
                channel, f"{self._module}.{self._class}.{_method}", f"Stopping streamelements event in {channel}"
            )
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if channel_settings is None:
                self.log.error(
                    channel,
                    f"{self._module}.{self._class}.{_method}",
                    f"No streamelements settings found for {channel}"
                )
                return
            if args is None or len(args) == 0:
                self.log.error(
                    channel, f"{self._module}.{self._class}.{_method}", f"No arguments provided for {channel}"
                )
                return

            tip_message = ' '.join(args[0:]).strip()
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings

            channel_settings[self.event_name]["tip_message"] = tip_message
            self.settings.set_channel_settings(self.db, channel, channel_settings)
            await ctx.reply(
                f"@{ctx.message.author.name} Your stream elements tip message has been set to '{tip_message}'. Use {prefix}streamelements tip <message> to change it."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())

    async def _streamelements_stop(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        channel = utils.clean_channel_name(ctx.channel.name)
        try:
            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    f"{self._module}.{self._class}.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(
                channel, f"{self._module}.{self._class}.{_method}", f"Stopping streamelements event in {channel}"
            )
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
                f"@{ctx.message.author.name}, I will no longer watch for stream elements events in your channel. You can start it again with `{prefix}streamelements start`."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())

    async def _streamelements_start(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        channel = utils.clean_channel_name(ctx.message.channel.name)
        try:
            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    f"{self._module}.{self._class}.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, f"{self._module}.{_method}", f"Starting streamelements event in {channel}")
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
                f"@{ctx.message.author.name}, I will now watch for stream elements events in your channel and give tacos to supporters. You can stop it with `{prefix}streamelements stop`."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())

    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    @commands.Cog.event(event="event_message")
    async def event_message(self, message: twitchio.Message) -> None:
        _method = inspect.stack()[0][3]
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            game_settings: dict[str, typing.Any] = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                return

            tip_pattern: str = game_settings.get("tip_message", self.default_settings["tip_message"])
            # replace {currency}{amount} with "(?P<tip>[¥$₡£¢]?\d{1,}(?:\.\d{1,})?)"
            tip_pattern = tip_pattern.replace("{currency}{amount}", r"(?P<tip>[¥$₡£¢]?\\d{1,}(?:\.\d{1,})?)")
            # replace {user} with "(?P<user>\w+)"
            tip_pattern = tip_pattern.replace("{user}", r"(?P<user>\w+)")
            tip_regex: re.Pattern = re.compile(tip_pattern, re.IGNORECASE | re.MULTILINE)

            if sender == channel:
                return

            # is the message from the bot?
            if sender == utils.clean_channel_name(self.event_name):
                # if message.content matches tip regex
                match = tip_regex.match(message.content)
                if match:
                    # get the tip amount
                    tip = match.group("tip")
                    if tip is None:
                        tip = "an unknown amount"
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            f"{self._module}.{self._class}.{_method}",
                            f"NON-TACO: {username} just tipped {tip} in {channel}'s channel",
                        )
                        return

                    reason = f"tipping {tip} in {channel}'s channel"
                    self.log.debug(channel, f"{self._module}.{self._class}.{_method}", f"{username} {reason}")
                    await self.tacos_log.give_user_tacos(
                        utils.clean_channel_name(self.settings.bot_name),
                        username,
                        reason,
                        give_type=tacotypes.TacoTypes.TWITCH_CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return
        except Exception as e:
            self.log.error(
                message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )


def prepare(bot) -> None:
    bot.add_cog(StreamElementsBotCog(bot))
