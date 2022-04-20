from .discord import webhook as discord_webhook
from . import settings
from . import loglevel
from . import logger
from . import tacotypes
from . import mongo

import traceback
import inspect

class TacosLog():
    def __init__(self, bot):
        self.settings = settings.Settings()
        self.bot = bot
        self.webhook = discord_webhook.DiscordWebhook(self.settings.discord_tacos_log_webhook_url)
        self.db = mongo.MongoDatabase()

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)


    async def _log(self, fromUser: str, toUser: str, amount: int, total_taco_count: int, reason: str = None):
        if amount == 0:
            return
        action = "given"
        action_adverb = "to"
        abs_amount = abs(amount)
        if amount < 0:
            action = "taken"
            action_adverb = "from"
        if reason is None:
            reason = "[no reason given]"
        taco_word = "taco"
        if amount != 1:
            taco_word = "tacos"

        total_taco_word = "taco"
        if total_taco_count != 1:
            total_taco_word = "tacos"

        content = f"{fromUser} has {action} {abs_amount} {taco_word} 🌮 {action_adverb} {toUser} for {reason}, giving them {total_taco_count} {total_taco_word} 🌮 total."

        # send to discord
        self.webhook.send(content)
        channels = [ fromUser ]
        # send to bot channels + the fromUser
        [ channels.append(f"{x.replace('#','').lower().strip()}") for x in self.settings.default_channels if x not in channels ]

        for c in channels:
            channel = self.bot.get_channel(c)
            if channel:
                await channel.send(content)

    async def give_user_tacos(self, fromUser: str, toUser: str, reason: str = None, give_type: tacotypes.TacoTypes = tacotypes.TacoTypes.CUSTOM, amount: int = 1):
        try:
            _method = inspect.stack()[0][3]
            # get taco settings
            taco_settings = self.settings.get_settings(self.db, "tacos")
            if not taco_settings:
                # raise exception if there are no tacos settings
                self.log.error(fromUser, "tacos.on_message", f"No tacos settings found for guild {self.settings.discord_guild_id}")
                return
            taco_count = amount

            if give_type != tacotypes.TacoTypes.CUSTOM:
                taco_count = taco_settings[tacotypes.TacoTypes.get_string_from_taco_type(give_type)]
            elif give_type == tacotypes.TacoTypes.CUSTOM:
                taco_count = amount
            else:
                self.log.warn(fromUser, "tacos.on_message", f"Invalid taco type {give_type}")
                return

            # only reject <= 0 tacos if it is not custom type
            if taco_count <= 0 and give_type != tacotypes.TacoTypes.CUSTOM:
                self.log.warn(fromUser, "tacos.on_message", f"Invalid taco count {taco_count}")
                return

            reason_msg = reason if reason else "no reason given" # self.settings.get_string(fromUser, 'no_reason')

            total_taco_count = self.db.add_tacos(toUser, taco_count)
            await self._log(fromUser, toUser, taco_count, total_taco_count, reason_msg)
            return total_taco_count
        except Exception as e:
            self.log.error(fromUser, _method, str(e), traceback.format_exc())
