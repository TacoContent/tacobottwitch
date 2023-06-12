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

# DixperBro:


class DixperBroCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 5
        self.bot_user = "dixperbro"
        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]

        self.default_settings = {
            "enabled": True,
            "purchase_regex": r"^(?P<user>\@?\w+)\shas\sbought\s(?P<amount>\d{1,})\s(?P<crate>(?:\w+\s?)+)",
            "gift_regex": r"^(?P<user>\@?\w+)\shas\sgifted\s(?P<amount>\d{1,})\s(?P<crate>(?:\w+\s?)+)(?:\sto\s(?P<gifted>\@?\w+))$"
        }

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "dixper.__init__", "Initialized")


    @commands.command(name="dixper")
    async def dixper(self, ctx: commands.Context, subcommand: str = None, *args) -> None:
        _method = inspect.stack()[1][3]

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
            self.log.debug(
                ctx.message.channel.name,
                f"dixper.{_method}",
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        if subcommand is not None:
            if subcommand.lower() in self.stop_commands:
                await self._dixper_stop(ctx, args)
            elif subcommand.lower() in self.start_commands:
                await self._dixper_start(ctx, args)

    async def _dixper_stop(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        try:
            channel = utils.clean_channel_name(ctx.channel.name)

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    f"dixper.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, "dixper.dixper_stop", f"Stopping dixper event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.bot_user not in channel_settings:
                channel_settings[self.bot_user] = self.default_settings

            channel_settings[self.bot_user]["enabled"] = False
            self.settings.set_channel_settings(self.db, channel, channel_settings)

            await ctx.reply(
                f"@{ctx.message.author.display_name}, I will no longer give tacos for people that purchase dixper packs in your channel. You can start it again with `{prefix}dixper start`."
            )
        except Exception as e:
            self.log.error(channel, "dixper.dixper_stop", str(e), traceback.format_exc())


    async def _dixper_start(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        try:
            channel = utils.clean_channel_name(ctx.message.channel.name)

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    f"dixper.{_method}",
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, "dixper.dixper_start", f"Starting dixper event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.bot_user not in channel_settings:
                channel_settings[self.bot_user] = self.default_settings
            channel_settings[self.bot_user]["enabled"] = True
            self.settings.set_channel_settings(self.db, channel, channel_settings)

            await ctx.reply(
                f"@{ctx.message.author.display_name}, I will now give tacos to people that purchase dixper packs in your channel. You can stop it with `{prefix}dixper stop`."
            )
        except Exception as e:
            self.log.error(channel, "dixper.dixper_start", str(e), traceback.format_exc())


    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.bot_user not in channel_settings:
                channel_settings[self.bot_user] = self.default_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            game_settings = channel_settings.get(self.bot_user, self.default_settings)
            if not game_settings.get("enabled", True):
                return

            if sender == channel:
                return

            # is the message from the dixper bot?
            if sender == utils.clean_channel_name(self.bot_user):
                # if message.content matches purchase regex
                purchase_regex = re.compile(game_settings.get("purchase_regex", self.default_settings["purchase_regex"]), re.IGNORECASE| re.MULTILINE)
                match = purchase_regex.match(message.content)
                if match:
                    # get the crate name
                    crate_name = match.group("crate")
                    # get the amount
                    amount = int(match.group("amount"))
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    crate_word = "crates"
                    if amount == 1:
                        crate_word = "crate"
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            "dixper.event_message",
                            f"NON-TACO: {username} purchased {amount} {crate_name} dixper {crate_word} in {channel}'s channel",
                        )
                        return

                    reason = f"purchasing {amount} {crate_name} dixper {crate_word} in {channel}'s channel"
                    self.log.debug(
                        channel,
                        "dixper.event_message",
                        f"{username} {reason}",
                    )
                    await self.tacos_log.give_user_tacos(
                        utils.clean_channel_name(self.settings.bot_name),
                        username,
                        reason,
                        give_type=tacotypes.TacoTypes.TWITCH_CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return

                # if message.content matches gift regex
                gift_regex = re.compile(game_settings.get("gift_regex", self.default_settings["gift_regex"]), re.IGNORECASE| re.MULTILINE)
                match = gift_regex.match(message.content)
                if match:
                    # get the crate name
                    crate_name = match.group("crate")
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # get the amount
                    amount = int(match.group("amount"))
                    # get the gifted user
                    gifted = utils.clean_channel_name(match.group("gifted"))
                    crate_word = "crates"
                    if amount == 1:
                        crate_word = "crate"
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            "dixper.event_message",
                            f"NON-TACO: {username} gifted {amount} {crate_name} dixper {crate_word} to {gifted} in {channel}'s channel",
                        )
                        return

                    reason = f"gifted {amount} {crate_name} dixper {crate_word} to {gifted} in {channel}'s channel"
                    self.log.debug(
                        channel,
                        "dixper.event_message",
                        f"{username} {reason}",
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
            self.log.error(message.channel.name, "dixper.event_message", str(e), traceback.format_exc())


def prepare(bot) -> None:
    bot.add_cog(DixperBroCog(bot))
