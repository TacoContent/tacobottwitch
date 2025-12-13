from bot.cogs.lib.tacotypes import TacoTypes


class TacosWebhookPayload:
    def __init__(self, guild_id: int, from_user: str, to_user: str, amount: int, reason: str, type: TacoTypes):
        self.guild_id = guild_id
        self.from_user = from_user
        self.to_user = to_user
        self.amount = amount
        self.reason = reason
        self.type = type

    def to_dict(self):
        return {
            "guild_id": self.guild_id,
            "from_user": self.from_user,
            "to_user": self.to_user,
            "amount": self.amount,
            "reason": self.reason,
            "type": TacoTypes.get_string_from_taco_type(self.type),
        }

    @staticmethod
    def from_dict(data: dict):
        return TacosWebhookPayload(
            guild_id=data["guild_id"],
            from_user=data["from_user"],
            to_user=data["to_user"],
            amount=data["amount"],
            reason=data["reason"],
            type=TacoTypes.get_from_string(data["type"]),
        )

    def __str__(self):
        return f"{self.from_user} gave {self.to_user} {self.amount} tacos for {self.reason}"
