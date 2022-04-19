import enum
import twitchio
import typing
from . import settings
from . import mongo

class PermissionLevel(enum.Enum):
    EVERYONE = 0
    FOLLOWER = 1
    SUBSCRIBER = 2
    VIP = 4
    MODERATOR = 8
    BROADCASTER = 16


class Permissions:

    def __init__(self):
        self.settings = settings.Settings()
        self.db = mongo.MongoDatabase()

    def has_linked_account(self, user: typing.Union[twitchio.Chatter,str] = None):
        if isinstance(user, twitchio.Chatter):
            user = user.name
        user = user.replace("@", "").strip()
        did = self.db.get_discord_id_for_twitch_username(user)
        return did is not None

    def has_permission(self, user: twitchio.Chatter, level: PermissionLevel = PermissionLevel.EVERYONE):
        def is_vip(user):
            return "vip" in user.badges
        user_level = PermissionLevel.FOLLOWER # Since cant check follower, everyone is a follower...

        if user.is_broadcaster:
            user_level = PermissionLevel.BROADCASTER
        elif user.is_mod:
            user_level = PermissionLevel.MODERATOR
        elif is_vip(user):
            user_level = PermissionLevel.VIP
        elif user.is_subscriber:
            user_level = PermissionLevel.SUBSCRIBER
        # elif user_context.is_follower:
        #     user_level = PermissionLevel.FOLLOWER
        else:
            user_level = PermissionLevel.FOLLOWER # Since cant check follower, everyone is a follower...

        return user_level.value >= level.value

    def in_command_restricted_channel(self, ctx):
        return self.settings.bot_restricted_channels and ctx.message.channel.name in self.settings.bot_restricted_channels
