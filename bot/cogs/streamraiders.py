import inspect
import os
import re
import traceback
import typing

from bot.cogs.lib import logger, loglevel, mongo, settings, utils, permissions, tacos_log, tacotypes
from twitchio.ext import commands


# StreamCaptainBot: inmax_cz just placed an Epic Bizarre Rogue on the battlefield!
# StreamCaptainBot: DarthMinos just purchased a GuyNameMike Archer for $5.00! Thank you for supporting the channel!
class StreamCaptainBotCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 2
        self.bot_user = "streamcaptainbot"

        self.event_name = "streamraiders"
        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]

        self.default_settings = {
            "enabled": True,
            "epic_regex": r"^(?P<user>\w+)\sjust\splaced\san\s(?P<name>Epic\s(?:\w+\s?)+?)\son\sthe\sbattlefield$",
            "purchase_regex": r"^(?P<user>\w+)\sjust\spurchased\sa\s(?P<name>(?:\w+\s?)+)\sfor\s\$",
        }

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    @commands.command(name="streamraiders")
    async def streamraiders(self, ctx: commands.Context, subcommand: typing.Optional[str] = None, *args) -> None:
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
                await self._streamraiders_stop(ctx, args)
            elif subcommand.lower() in self.start_commands:
                await self._streamraiders_start(ctx, args)

    async def _streamraiders_stop(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        channel = utils.clean_channel_name(ctx.channel.name)
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

            self.log.debug(
                channel, f"{self._module}.{self._class}.{_method}", f"Stopping streamraiders event in {channel}"
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
                f"@{ctx.message.author.name}, I will no longer give tacos if someone places an epic on the battlefield in streamraiders. You can start it again with `{prefix}streamraiders start`."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())

    async def _streamraiders_start(self, ctx: commands.Context, args) -> None:
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

            self.log.debug(
                channel, f"{self._module}.{self._class}.{_method}", f"Starting streamraiders event in {channel}"
            )
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
                f"@{ctx.message.author.name}, I will now give tacos if someone places an epic on the battlefield in streamraiders. You can stop it again with `{prefix}streamraiders stop`."
            )
        except Exception as e:
            self.log.error(channel, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())

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
            game_settings = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                return

            if sender == channel:
                return

            # is the message from the bot?
            if sender == utils.clean_channel_name(self.bot_user):
                # if message.content matches epic regex
                epic_regex = re.compile(game_settings.get("epic_regex", self.default_settings["epic_regex"]), re.IGNORECASE | re.MULTILINE)
                match = epic_regex.match(message.content)
                if match:
                    # get the epic name
                    epic_name = match.group("name")
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            f"{self._module}.{_method}",
                            f"NON-TACO: {username} placed a StreamRaiders {epic_name} in {channel}'s channel",
                        )
                        return

                    reason = f"placing a StreamRaiders {epic_name} in @{channel}'s channel"
                    self.log.debug(
                        channel,
                        f"{self._module}.{_method}",
                        f"{username} placed a StreamRaiders {epic_name} in {channel}'s channel",
                    )
                    await self.tacos_log.give_user_tacos(
                        fromUser=utils.clean_channel_name(self.bot.nick),
                        toUser=username,
                        reason=reason,
                        give_type=tacotypes.TacoTypes.TWITCH_CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return

                # if message.content matches purchase regex
                purchase_regex = re.compile(
                    game_settings.get("purchase_regex", self.default_settings["purchase_regex"]),
                    re.IGNORECASE | re.MULTILINE,
                )
                match = purchase_regex.match(message.content)
                if match:
                    # get the epic name
                    skin_name = match.group("name")
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            f"{self._module}.{self._class}.{_method}",
                            f"NON-TACO: {username} purchased a StreamRaiders {skin_name} skin in {channel}'s channel",
                        )
                        return

                    reason = f"purchasing a StreamRaiders {skin_name} skin in @{channel}'s channel"
                    self.log.debug(
                        channel,
                        f"{self._module}.{_method}",
                        f"{username} purchased a StreamRaiders {skin_name} skin in {channel}'s channel",
                    )
                    await self.tacos_log.give_user_tacos(
                        fromUser=utils.clean_channel_name(self.bot.nick),
                        toUser=username,
                        reason=reason,
                        give_type=tacotypes.TacoTypes.TWITCH_CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return
        except Exception as e:
            self.log.error(
                message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )


def prepare(bot) -> None:
    bot.add_cog(StreamCaptainBotCog(bot))
