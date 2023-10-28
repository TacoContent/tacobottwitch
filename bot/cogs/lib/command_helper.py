import typing

from bot.cogs.lib import permissions
from twitchio import Chatter


async def check_linked_account(ctx, user: typing.Optional[typing.Union[Chatter, str]] = None) -> bool:
    perm = permissions.Permissions()
    if user is None:
        username = ctx.message.author
        mention = ctx.message.author.mention
    if isinstance(user, Chatter):
        mention = user.mention
        username = user.name
    else:
        username = user
        mention = f"@{username}"

    if not perm.has_linked_account(user):
        await ctx.reply(f"{mention}, You must link your account with me first!\nUse `!taco link` to link your account.")
        return False
    return True
