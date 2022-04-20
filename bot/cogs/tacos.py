from dataclasses import replace
from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect
from .lib import mongo
from .lib import settings
from .lib import logger
from .lib import loglevel
from .lib import permissions
from .lib import command_helper
from .lib import tacos_log as tacos_log
from .lib import tacotypes

class TacosCog(commands.Cog):
    """Allows the streamer to give a user tacos"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.subcommands = ["give", "take", "balance", "count", "top", "leaderboard", "help"]
        self.permissions_helper = permissions.Permissions()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)

        self.log.debug("NONE", "tacos.__init__", "Initialized")

    @commands.command(name="tacos")
    async def tacos(self, ctx, subcommand: str = None, *args):
        _method = inspect.stack()[1][3]

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
            self.log.debug(
                ctx.message.channel.name,
                _method,
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        if subcommand in self.subcommands:
            if subcommand == "give":
                await self._tacos_give(ctx, args)
            elif subcommand == "take":
                await self._tacos_take(ctx, args)
            elif subcommand == "balance" or subcommand == "bal" or subcommand == "count":
                await self._tacos_balance(ctx, args)
            elif subcommand == "top" or subcommand == "leaderboard" or subcommand == "lb":
                print("calling leaderboard")
                await self._tacos_top(ctx, args)
            else:
                await self._tacos_help(ctx, args)
        else:
            await self._tacos_help(ctx, args)

    async def _tacos_top(self, ctx, args):
        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return
        try:
            limit = 5

            if len(args) >= 1:
                limit = int(args[0])
                if limit > 10:
                    limit = 10
                elif limit < 1:
                    limit = 1

            # user command
            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
                self.log.debug(
                    ctx.message.channel.name,
                    _method,
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return
            lb = self.db.get_top_tacos_leaderboard(limit=limit)
            message_out = "Tacos Leaderboard: "
            index_position = 1
            for i in lb:

                taco_count = i["count"]
                taco_word = "taco"
                if taco_count != 1:
                    taco_word = "tacos"

                message_out += f"::{index_position}:: {i['user']['twitch_name']} <-> {taco_count} {taco_word} 🌮 "
                if index_position < limit:
                    message_out += " -> "
                index_position = index_position + 1
            await ctx.reply(message_out)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    async def _tacos_balance(self, ctx, args):
        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return
        try:
            if len(args) >= 1:
                # mod command
                if not self.permissions_helper.has_permission(
                    ctx.message.author, permissions.PermissionLevel.MODERATOR
                ):
                    self.log.debug(
                        ctx.message.channel.name,
                        _method,
                        f"{ctx.message.author.name} does not have permission to use this command.",
                    )
                    return
                user = args[0].lower().replace("@", "").strip()
                await self._tacos_balance_for_user(ctx, user)
            elif len(args) == 0:
                # user command
                if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
                    self.log.debug(
                        ctx.message.channel.name,
                        _method,
                        f"{ctx.message.author.name} does not have permission to use this command.",
                    )
                    return
                await self._tacos_balance_for_user(ctx, ctx.message.author.name)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    async def _tacos_balance_for_user(self, ctx, user):
        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return
        if not await command_helper.check_linked_account(ctx, user):
            return

        try:
            if user == ctx.message.author.name:
                response_user = "you"
                response_has = "have"
            else:
                response_user = user
                response_has = "has"
            user_tacos = self.db.get_tacos_count(user)
            if user_tacos:
                taco_word = "taco"
                if user_tacos != 1:
                    taco_word = "tacos"
                await ctx.reply(f"{response_user} {response_has} {user_tacos} {taco_word} 🌮.")
            else:
                await ctx.reply(f"{response_user} {response_has} no tacos 🌮.")
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    async def _tacos_give(self, ctx, args):
        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
            self.log.debug(
                ctx.message.channel.name,
                _method,
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        channel = self.bot.get_channel(ctx.message.channel.name)
        if not channel:
            self.log.debug(ctx.message.channel.name, _method, f"Channel {ctx.message.channel.name} not found.")
            return

        if len(args) >= 2:
            user = args[0].lower().replace("@", "").strip()
            if not await command_helper.check_linked_account(ctx, user):
                return

            amount = args[1]
            reason = "just being awesome"
            if len(args) > 2:
                reason = " ".join(args[2:])
            if amount.isdigit():
                amount = int(amount)
                if amount > 0:
                    await self.tacos_log.give_user_tacos(ctx.message.channel.name, user, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=amount)
                else:
                    await ctx.send(f"You can't give negative tacos!")
            else:
                await ctx.send(f"{amount} is not a valid number!")
        else:
            await self._tacos_help(ctx, args)

    async def _tacos_take(self, ctx, args):
        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
            self.log.debug(
                ctx.message.channel.name,
                _method,
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        channel = self.bot.get_channel(ctx.message.channel.name)
        if not channel:
            self.log.debug(ctx.message.channel.name, _method, f"Channel {ctx.message.channel.name} not found.")
            return

        if len(args) >= 2:
            user = args[0].lower().replace("@", "").strip()
            if not await command_helper.check_linked_account(ctx, user):
                return
            amount = args[1]
            reason = "[no reason given]"
            if len(args) > 2:
                reason = " ".join(args[2:])
            if amount.isdigit():
                amount = int(amount)
                if amount > 0:
                    await self.tacos_log.give_user_tacos(ctx.message.channel.name, user, reason, give_type=tacotypes.TacoTypes.CUSTOM, amount=-(amount))
                else:
                    await ctx.send(f"You can't take negative tacos!")
            else:
                await ctx.send(f"{amount} is not a valid number!")
        else:
            await self._t

    async def _tacos_help(self, ctx, args):
        if ctx.message.echo:
            return
        await ctx.send(f"Usage: !taco tacos [command] [args]")


def prepare(bot):
    bot.add_cog(TacosCog(bot))
