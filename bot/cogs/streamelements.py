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


class StreamElementsBotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 5

        self.bot_user = "streamelements"
        self.tip_regex = re.compile(
            r"^(?P<user>\w+)\s(?:just\s)?tipped\s(?P<tip>[¥$₡£¢]?\d{1,}(?:\.\d{1,})?)", re.MULTILINE | re.IGNORECASE
        )

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "streamelements.__init__", "Initialized")

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

            # is the message from the bot?
            if sender == utils.clean_channel_name(self.bot_user):
                # if message.content matches tip regex
                match = self.tip_regex.match(message.content)
                if match:
                    # get the tip amount
                    tip = match.group("tip")
                    # get the user
                    username = utils.clean_channel_name(match.group("user"))
                    # if the user is a known taco user, give tacos
                    if not self.permissions_helper.has_linked_account(username):
                        self.log.debug(
                            channel,
                            "streamelements.event_message",
                            f"NON-TACO: {username} just tipped {tip} in {channel}'s channel",
                        )
                        return

                    reason = f"tipping {tip} in {channel}'s channel"
                    self.log.debug(
                        channel,
                        "streamelements.event_message",
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
            self.log.error(message.channel.name, "streamelements.event_message", str(e), traceback.format_exc())
def prepare(bot):
    bot.add_cog(StreamElementsBotCog(bot))
