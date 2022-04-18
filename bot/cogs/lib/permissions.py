from typing import TypeVar
from twitchio.ext import commands
import twitchio
import enum

class Permissions(enum.Enum):
    EVERYONE = 0
    TURBO = 1
    FOLLOWER = 2
    SUBSCRIBER = 4
    VIP = 8
    MODERATOR = 16
    BROADCASTER = 32

FN = TypeVar("FN")
def has_permission(permission: Permissions = Permissions.EVERYONE):
    def decorator(func: FN) -> FN:
        def check_vip(ctx):
                if ctx.message.echo:
                    return True
                return "vip" in ctx.message.author.badges
        def check_follower(ctx):
                if ctx.message.echo:
                    return True
                # return ctx.message.author.is_follower or ctx.message.author.is_subscriber
                return True
        def check_subscriber(ctx):
                if ctx.message.echo:
                    return True
                return ctx.message.author.is_subscriber or ctx.message.author.is_mod or ctx.message.author.is_broadcaster
        def check_moderator(ctx):
                if ctx.message.echo:
                    return True
                return ctx.message.author.is_mod or ctx.message.author.is_broadcaster
        def check_broadcaster(ctx):
                if ctx.message.echo:
                    return True
                return ctx.message.author.is_broadcaster
        if isinstance(func, commands.Command):
            if permission == Permissions.EVERYONE:
                return True
            if permission == Permissions.FOLLOWER:
                return check_follower(ctx)
        else:
            pass
        return func

    return decorator

async def has_permission(*args, **kwargs):
    def predicate(func):
        async def wrapper(*args, **kwargs):
            ctx = kwargs['ctx']
            def check_vip(ctx):
                if ctx.message.echo:
                    return True
                return "vip" in ctx.message.author.badges

            if ctx.message.echo:
                return await func(*args, **kwargs)

            if 'permission' not in kwargs:
                kwargs['permission'] = Permssions.EVERYONE

            if kwargs['permission'] == Permssions.EVERYONE:
                return await func(*args, **kwargs)

            if kwargs['permission'] == Permssions.FOLLOWER:
                if ctx.message.author.is_follower or ctx.message.author.is_subscriber:
                    return await func(*args, **kwargs)
            if kwargs['permission'] == Permssions.SUBSCRIBER:
                if ctx.message.author.is_subscriber:
                    return await func(*args, **kwargs)
            if kwargs['permission'] == Permssions.VIP:
                if check_vip(ctx) or ctx.message.author.is_mod or ctx.message.author.is_broadcaster:
                    return await func(*args, **kwargs)
            if kwargs['permission'] == Permssions.MODERATOR:
                if ctx.message.author.is_mod or ctx.message.author.is_broadcaster:
                    return await func(*args, **kwargs)
            if kwargs['permission'] == Permssions.BROADCASTER:
                if ctx.message.author.is_broadcaster:
                    return await func(*args, **kwargs)
            raise commands.CommandError(f"You do not have permission to use this command.")
        return wrapper
    return predicate
