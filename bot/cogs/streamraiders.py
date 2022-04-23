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

# StreamCaptainBot: inmax_cz just placed an Epic Bizarre Rogue on the battlefield!
# StreamCaptainBot: DarthMinos just purchased a GuyNameMike Archer for $5.00! Thank you for supporting the channel!


class StreamCaptainBotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)

        self.stream_captain_bot = "streamcaptainbot"
        self.epic_regex = re.compile(
            r"^(?P<user>\w+)\sjust\splaced\san\s(?P<name>Epic\s(?:\w+\s?)+?)\son\sthe\sbattlefield"
        )
        self.purchase_regex = re.compile(r"^(?P<user>\w+)\sjust\spurchased\sa\s(?P<name>(?:\w+\s?)+)\sfor\s\$")

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "streamraiders.__init__", "Initialized")

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)
            # is the message from the bot?
            if sender == utils.clean_channel_name(self.stream_captain_bot):
                # if message.content matches epic regex
                match = self.epic_regex.match(message.content)
                if match:
                    # get the epic name
                    epic_name = match.group("name")
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            "streamraiders.event_message",
                            f"NON-TACO: {username} placed a StreamRaiders {epic_name} in {channel}'s channel",
                        )
                        return

                    reason = f"placing a StreamRaiders {epic_name} in {channel}'s channel"
                    self.log.debug(
                        channel,
                        "streamraiders.event_message",
                        f"{username} placed a StreamRaiders {epic_name} in {channel}'s channel",
                    )
                    await self.tacos_log.give_user_tacos(
                        self.settings.bot_name, username, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=5
                    )

                # if message.content matches purchase regex
                match = self.purchase_regex.match(message.content)
                if match:
                    # get the epic name
                    skin_name = match.group("name")
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            "streamraiders.event_message",
                            f"NON-TACO: {username} purchased a StreamRaiders {skin_name} skin in {channel}'s channel",
                        )
                        return

                    reason = f"purchasing a StreamRaiders {skin_name} skin in {channel}'s channel"
                    self.log.debug(
                        channel,
                        "streamraiders.event_message",
                        f"{username} purchased a StreamRaiders {skin_name} skin in {channel}'s channel",
                    )
                    await self.tacos_log.give_user_tacos(
                        self.settings.bot_name, username, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=5
                    )
        except Exception as e:
            self.log.error(message.channel.name, "streamraiders.event_message", str(e), traceback.format_exc())


def prepare(bot):
    bot.add_cog(StreamCaptainBotCog(bot))
