import inspect
import os
import traceback
import typing

from bot.cogs.lib import logger, loglevel, mongo, settings, tacotypes, utils
from bot.cogs.lib.tacobot.tacos_payload import TacosWebhookPayload
from bot.cogs.lib.tacobot.webhook import TacobotWebhook

class TacosLog:
    def __init__(self, bot):
        _method = inspect.stack()[0][3]
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self._class = self.__class__.__name__
        self.settings = settings.Settings()
        self.bot = bot
        self.tacos_webhook = TacobotWebhook(f"{self.settings.tacobot_webhook_url}webhook/tacos", self.settings.tacobot_webhook_token)
        self.db = mongo.MongoDatabase()

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)

    async def _log(
        self, fromUser: str, toUser: str, amount: int, total_taco_count: int, reason: typing.Optional[str] = None
    ) -> None:
        _method = inspect.stack()[0][3]
        if amount == 0:
            return
        action = "received"
        action_adverb = "from"
        abs_amount = abs(amount)
        if amount < 0:
            action = "lost"
        if reason is None:
            reason = "[no reason given]"
        taco_word = "taco"
        if amount != 1:
            taco_word = "tacos"

        total_taco_word = "taco"
        if total_taco_count != 1:
            total_taco_word = "tacos"

        content = f"@{toUser} has {action} {abs_amount} {taco_word} 🌮 {action_adverb} @{fromUser} for {reason}, giving them {total_taco_count} {total_taco_word} 🌮 total."

        channels = [utils.clean_channel_name(fromUser)]
        # send to bot channels + the fromUser
        [
            channels.append(f"{utils.clean_channel_name(x)}")
            for x in self.settings.default_channels
            if utils.clean_channel_name(x) not in channels
        ]

        for c in channels:
            try:
                channel = self.bot.get_channel(c)
                if channel:
                    if content:
                        await channel.send(content)
            except Exception as e:
                self.log.error(c, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc())

    async def give_user_tacos(
        self,
        fromUser: str,
        toUser: str,
        reason: typing.Optional[str] = None,
        give_type: tacotypes.TacoTypes = tacotypes.TacoTypes.TWITCH_CUSTOM,
        amount: int = 1,
    ):
        _method = inspect.stack()[0][3]
        try:
            # get taco settings
            taco_settings = self.settings.get_settings(self.db, "tacos")
            if not taco_settings:
                # raise exception if there are no tacos settings
                self.log.error(
                    fromUser,
                    f"{self._module}.{_method}",
                    f"No tacos settings found for guild {self.settings.discord_guild_id}",
                )
                return
            taco_count = amount

            taco_type_key = tacotypes.TacoTypes.get_string_from_taco_type(give_type)
            if taco_type_key not in taco_settings:
                self.log.debug(
                    fromUser,
                    f"{self._module}.{_method}",
                    f"Key {taco_type_key} not found in taco settings. Using taco_amount ({amount}) as taco count",
                )
                taco_count = taco_count
            else:
                taco_count = taco_settings[taco_type_key]
            reason_msg = reason if reason else "no reason given"

            result = self.tacos_webhook.send_payload(
                TacosWebhookPayload(
                    guild_id=self.settings.discord_guild_id,
                    from_user=fromUser,
                    to_user=toUser,
                    amount=taco_count,
                    reason=reason_msg,
                    type=give_type,
                ).to_dict()
            )
            if result is None:
                self.log.error(fromUser, f"{self._module}.{_method}", "Error sending webhook")
                return None

            if "error" in result:
                self.log.error(fromUser, f"{self._module}.{_method}", result["error"])
                return None

            total_taco_count = result["total_tacos"]

            await self._log(fromUser, toUser, taco_count, total_taco_count, reason_msg)

            return total_taco_count
        except Exception as e:
            self.log.error(fromUser, f"{self._module}.{_method}", str(e), traceback.format_exc())
