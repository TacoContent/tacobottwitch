import enum
import typing

import twitchio
from bot.cogs.lib import mongo, settings, utils


class PermissionLevel(enum.Enum):
    EVERYONE = 0
    FOLLOWER = 1
    SUBSCRIBER = 2
    VIP = 4
    MODERATOR = 8
    BROADCASTER = 16

    BOT = 512
    BOT_OWNER = 1024


class Permissions:
    def __init__(self):
        self.settings = settings.Settings()
        self.db = mongo.MongoDatabase()

    def has_linked_account(
        self, user: typing.Optional[typing.Union[twitchio.Chatter, twitchio.PartialChatter, str]] = None
    ) -> bool:
        if isinstance(user, twitchio.Chatter) or isinstance(user, twitchio.PartialChatter):
            username = user.name
        else:
            username = user
        username = utils.clean_channel_name(username)
        did = self.db.get_discord_id_for_twitch_username(username)
        return did is not None

    def has_permission(
        self,
        user: typing.Union[twitchio.Chatter, twitchio.PartialChatter],
        level: PermissionLevel = PermissionLevel.EVERYONE,
    ) -> bool:

        def is_vip(user):
            return "vip" in user.badges

        def is_bot_owner(user):
            return utils.clean_channel_name(user.name) == utils.clean_channel_name(self.settings.bot_owner)

        def is_bot(user):
            return utils.clean_channel_name(user.name) == utils.clean_channel_name(self.settings.bot_name)

        user_level = PermissionLevel.FOLLOWER  # Since cant check follower, everyone is a follower...
        if is_bot_owner(user):
            user_level = PermissionLevel.BOT_OWNER
        elif is_bot(user):
            user_level = PermissionLevel.BOT
        # if user object has is_broadcaster
        elif isinstance(user, twitchio.Chatter) and user.is_broadcaster:
            user_level = PermissionLevel.BROADCASTER
        elif isinstance(user, twitchio.Chatter) and user.is_mod:
            user_level = PermissionLevel.MODERATOR
        elif is_vip(user):
            user_level = PermissionLevel.VIP
        elif isinstance(user, twitchio.Chatter) and user.is_subscriber:
            user_level = PermissionLevel.SUBSCRIBER
        # elif user_context.is_follower:
        #     user_level = PermissionLevel.FOLLOWER
        else:
            user_level = PermissionLevel.FOLLOWER  # Since cant check follower, everyone is a follower...

        return user_level.value >= level.value

    def in_command_restricted_channel(self, ctx):
        return (
            self.settings.bot_restricted_channels
            and utils.clean_channel_name(ctx.message.channel.name) in self.settings.bot_restricted_channels
        )
