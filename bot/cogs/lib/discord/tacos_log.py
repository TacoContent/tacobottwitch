from . import webhook as discord_webhook
from .. import settings

class TacosLog():
    def __init__(self):
        self.settings = settings.Settings()

        self.webhook = discord_webhook.DiscordWebhook(self.settings.discord_tacos_log_webhook_url)
    def send(self, fromUser: str, toUser: str, amount: int, reason: str = None):
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
        if amount > 1:
            taco_word = "tacos"

        content = f"{fromUser} has {action} {abs_amount} {taco_word} 🌮 {action_adverb} {toUser} for {reason}."
        self.webhook.send(content)
