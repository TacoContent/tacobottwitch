import inspect
import os
import traceback
import typing

from bot.cogs.lib import command_helper, logger, loglevel, mongo, permissions, settings, tacos_log, tacotypes, utils
from twitchio.ext import commands


class TacosCog(commands.Cog):
    """Allows the streamer to give a user tacos"""

    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.subcommands = ["give", "take", "balance", "bal", "count", "top", "leaderboard", "lb", "help"]

        self.permissions_helper = permissions.Permissions()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)

        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

    @commands.command(name="tacos")
    async def tacos(self, ctx, subcommand: typing.Optional[str] = None, *args) -> None:
        _method = inspect.stack()[1][3]

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{_method}",
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        if subcommand in self.subcommands:
            if subcommand.lower() == "give":
                await self._tacos_give(ctx, args)
            elif subcommand.lower() == "take":
                await self._tacos_take(ctx, args)
            elif subcommand.lower() == "balance" or subcommand.lower() == "bal" or subcommand.lower() == "count":
                await self._tacos_balance(ctx, args)
            elif subcommand.lower() == "top" or subcommand.lower() == "leaderboard" or subcommand.lower() == "lb":
                await self._tacos_top(ctx, args)
            elif subcommand.lower() == "help":
                await self._tacos_help(ctx, args)
            else:
                await self._tacos_balance(ctx, args)
        else:
            await self._tacos_balance(ctx, args)

    async def _tacos_top(self, ctx, args) -> None:
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
                    f"{self._module}.{_method}",
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
            self.log.error(ctx.message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())

    async def _tacos_balance(self, ctx, args) -> None:
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
                        f"{self._module}.{_method}",
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
                        f"{self._module}.{_method}",
                        f"{ctx.message.author.name} does not have permission to use this command.",
                    )
                    return
                await self._tacos_balance_for_user(ctx, ctx.message.author.name)
        except Exception as e:
            self.log.error(ctx.message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())

    async def _tacos_balance_for_user(self, ctx, user) -> None:
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
                response_user = utils.clean_channel_name(user)
                response_has = "has"
            user_tacos = self.db.get_tacos_count(user)
            if user_tacos:
                taco_word = "taco"
                if user_tacos != 1:
                    taco_word = "tacos"
                await ctx.reply(
                    f"@{ctx.message.author.display_name}, {response_user} {response_has} {user_tacos} {taco_word} 🌮."
                )
            else:
                await ctx.reply(f"@{ctx.message.author.display_name}, {response_user} {response_has} no tacos 🌮.")
        except Exception as e:
            self.log.error(ctx.message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())

    async def _tacos_give(self, ctx, args) -> None:
        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return

        ## Need to track how many tacos the user has given.
        ## If they give more than 500 in 24 hours, they can't give anymore.
        max_give_per_day = 500
        ## Limit the number they can give to a specific user in 24 hours.
        max_give_per_user_per_day = 50
        ## Limit the number they can give to a user at a time.
        max_give_per_user = 10

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{_method}",
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        channel = self.bot.get_channel(ctx.message.channel.name)
        if not channel:
            self.log.debug(
                ctx.message.channel.name, f"{self._module}.{_method}", f"Channel {ctx.message.channel.name} not found."
            )
            return

        if len(args) >= 2:
            user = utils.clean_channel_name(args[0])

            if user == utils.clean_channel_name(ctx.message.channel.name) or user == utils.clean_channel_name(
                ctx.message.author.name
            ):
                await ctx.reply(
                    f"@{ctx.message.author.display_name}, you can't give yourself (or {ctx.message.channel.name}) tacos."
                )
                return

            ## Give all users tacos??
            ## should this be implemented? I don't think so.

            amount = args[1]
            if amount.isdigit():
                amount = int(amount)

                if not await command_helper.check_linked_account(ctx, user):
                    return

                total_gifted_to_user = self.db.get_total_gifted_tacos_to_user(
                    utils.clean_channel_name(ctx.message.channel.name),
                    utils.clean_channel_name(ctx.message.author.name),
                    86400,
                )
                remaining_gifts_to_user = max_give_per_user_per_day - total_gifted_to_user

                if remaining_gifts_to_user < 1:
                    await ctx.reply(
                        f"@{ctx.message.author.display_name}, you have reached the maximum number of tacos you can give to {user} in a rolling 24 hours."
                    )
                    return
                elif remaining_gifts_to_user < amount:
                    await ctx.reply(
                        f"@{ctx.message.author.display_name}, you can only give {remaining_gifts_to_user} tacos to {user} in a rolling 24 hours."
                    )
                    return

                total_gifted_24_hours = self.db.get_total_gifted_tacos(
                    utils.clean_channel_name(ctx.message.channel.name), 86400
                )
                remaining_gifts_24_hours = max_give_per_day - total_gifted_24_hours
                if remaining_gifts_24_hours < 1:
                    await ctx.reply(
                        f"@{ctx.message.author.display_name}, you have reached the maximum number of tacos you can give in a rolling 24 hours."
                    )
                    return
                elif remaining_gifts_24_hours < amount:
                    await ctx.reply(
                        f"@{ctx.message.author.display_name}, you can only have {remaining_gifts_24_hours} tacos you can give out in a rolling 24 hours."
                    )
                    return

                reason = "just being awesome"
                if len(args) > 2:
                    reason = " ".join(args[2:])

                if amount > max_give_per_user:
                    await ctx.reply(
                        f"@{ctx.message.author.display_name}, you can only give a maximum of {max_give_per_user} tacos at a time."
                    )
                    return

                if amount > 0:
                    await self.tacos_log.give_user_tacos(
                        fromUser=ctx.message.channel.name,
                        toUser=user,
                        reason=reason,
                        give_type=tacotypes.TacoTypes.TWITCH_RECEIVE_TACOS,
                        amount=amount,
                    )

                    # don't need to check if the user has permissions, since we do that above.

                    # give the broadcaster 5 tacos for using the command.
                    taco_word = "taco" if amount == 1 else "tacos"

                    await self.tacos_log.give_user_tacos(
                        fromUser=utils.clean_channel_name(self.settings.bot_name),
                        toUser=utils.clean_channel_name(ctx.message.channel.name),
                        reason=f"giving {user} {amount} {taco_word} 🌮",
                        give_type=tacotypes.TacoTypes.TWITCH_GIVE_TACOS,
                        amount=amount,
                    )

                else:
                    await ctx.send(f"You can't give negative tacos!")
            else:
                await ctx.send(f"{amount} is not a valid number!")
        else:
            await self._tacos_help(ctx, args)

    async def _tacos_take(self, ctx, args) -> None:
        max_take_per_user = 5

        _method = inspect.stack()[1][3]
        if ctx.message.echo:
            return

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{_method}",
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        channel = self.bot.get_channel(ctx.message.channel.name)
        if not channel:
            self.log.debug(
                ctx.message.channel.name, f"{self._module}.{_method}", f"Channel {ctx.message.channel.name} not found."
            )
            return

        if len(args) >= 2:
            user = utils.clean_channel_name(args[0])
            if not await command_helper.check_linked_account(ctx, user):
                return
            amount = args[1]
            reason = "[no reason given]"
            if len(args) > 2:
                reason = " ".join(args[2:])
            if amount.isdigit():
                amount = int(amount)
                if amount > max_take_per_user:
                    await ctx.reply(
                        f"@{ctx.message.author.display_name}, you can only take a maximum of {max_take_per_user} tacos at a time."
                    )
                    return
                if amount > 0 and amount <= max_take_per_user:
                    await self.tacos_log.give_user_tacos(
                        ctx.message.channel.name,
                        user,
                        reason,
                        give_type=tacotypes.TacoTypes.TWITCH_CUSTOM,
                        amount=-(amount),
                    )
                else:
                    await ctx.send(f"You can't take negative or more than {max_take_per_user} tacos!")
            else:
                await ctx.send(f"{amount} is not a valid number!")
        else:
            await self._tacos_help(ctx, args)

    async def _tacos_help(self, ctx, args) -> None:
        if ctx.message.echo:
            return
        await ctx.send(f"Usage: !taco tacos [command] [args]. Available Commands: {', '.join(self.subcommands)}")

    def get_tacos_settings(self) -> dict:
        cog_settings = self.settings.get_settings(self.db, "tacos")
        if not cog_settings:
            raise Exception(f"No tacos settings found for guild {self.settings.discord_guild_id}")
        return cog_settings


def prepare(bot) -> None:
    bot.add_cog(TacosCog(bot))
