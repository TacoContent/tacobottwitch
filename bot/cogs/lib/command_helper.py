
import twitchio
from . import permissions
import typing

async def check_linked_account(ctx, user: typing.Union[twitchio.Chatter, str] = None) -> bool:
    perm = permissions.Permissions()
    if user is None:
        user = ctx.message.author
    if isinstance(user, twitchio.Chatter):
        user = user.name
        mention = user.mention
    else:
        mention = f"@{user}"

    if not perm.has_linked_account(user):
        await ctx.reply(f"{mention}, You must link your account with me first!\nUse `!taco link` to link your account.")
        return False
    return True
