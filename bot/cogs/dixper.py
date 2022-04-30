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
    def __init__(self, bot: commands.Bot):

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 5
        self.bot_user = "dixperbro"

        self.purchase_regex = re.compile(
            r"^(?P<user>\@?\w+)\shas\sbought\s(?P<amount>\d{1,})\s(?P<crate>(?:\w+\s?)+)", re.MULTILINE | re.IGNORECASE
        )
        self.gift_regex = re.compile(
            r"^(?P<user>\@?\w+)\shas\sgifted\s(?P<amount>\d{1,})\s(?P<crate>(?:\w+\s?)+)(?:\sto\s(?P<gifted>\@?\w+))$",
            re.MULTILINE | re.IGNORECASE,
        )
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "dixper.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            game_settings = channel_settings.get(self.bot_user, { "enabled": True })
            if not game_settings.get("enabled", True):
                return

            if sender == channel:
                return

            # is the message from the dixper bot?
            if sender == utils.clean_channel_name(self.bot_user):
                # if message.content matches purchase regex
                match = self.purchase_regex.match(message.content)
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
                        give_type=tacotypes.TacoTypes.CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return

                # if message.content matches gift regex
                match = self.gift_regex.match(message.content)
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
                        give_type=tacotypes.TacoTypes.CUSTOM,
                        amount=self.TACO_AMOUNT,
                    )
                    return

        except Exception as e:
            self.log.error(message.channel.name, "dixper.event_message", str(e), traceback.format_exc())


def prepare(bot):
    bot.add_cog(DixperBroCog(bot))
