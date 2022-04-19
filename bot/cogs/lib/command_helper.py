
import twitchio
from . import permissions

async def check_linked_account(ctx, user: twitchio.Chatter = None):
    perm = permissions.Permissions()
    if user is None:
        user = ctx.message.author
    if not perm.has_linked_account(user):
        await ctx.reply(f"{user.mention}, You must link your account with me first!\nUse `!taco link` to link your account.")
        return False
    return True
