import inspect
import os
import traceback
import typing

from bot.cogs.lib import loglevel, logger, mongo, permissions, settings, tacos_log, tacotypes, utils
from twitchio.ext import commands

class TacoInviteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()

        self.invite_message = "🌮🌮🌮 Join an amazing discord community that I am passionate about. TACO - The Alliance Collective Order - Tacos Aren't Just For Tuesday 🌮🌮🌮 -> Discord: {{url}} -> Twitch Team: https://twitch.tv/team/{{team}} -> Twitter: https://www.twitter.com/OurTaco"
        self.log.debug("NONE", f"{self._module}.{self._class}.{_method}", "Initialized")

    @commands.command(name="discord", aliases=["taco"])
    @commands.cooldown(1, 30, commands.Bucket.channel)
    async def discord(self, ctx) -> None:
        _method = inspect.stack()[1][3]

        try:
            if ctx.message.echo:
                return

            invite_data = self.db.get_invite_for_user(ctx.message.channel.name)
            if invite_data is None:
                invite_data = self.db.get_any_invite()

            if invite_data is None:
                await ctx.send(
                    f"I was unable to find an invite code to use for {ctx.message.channel.name}. Please create an invite in discord and try again."
                )
                return
            else:
                url = invite_data["info"]["url"]
                msg = utils.str_replace(self.invite_message, url=url, team=self.settings.twitch_team_name)

                # if the user is a moderator, give the broadcaster tacos for using the command.
                if self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                    # give the broadcaster 5 tacos for using the command.
                    taco_settings = self.get_tacos_settings()
                    promote_taco_amount = taco_settings.get(
                        tacotypes.TacoTypes.get_string_from_taco_type(tacotypes.TacoTypes.TWITCH_PROMOTE), 10
                    )

                    # give to the broadcaster from the bot. no notification in broadcaster channel.
                    await self.tacos_log.give_user_tacos(
                        fromUser=utils.clean_channel_name(self.bot.nick),
                        toUser=utils.clean_channel_name(ctx.message.channel.name),
                        reason="promoting TACO discord",
                        give_type=tacotypes.TacoTypes.TWITCH_PROMOTE,
                        amount=promote_taco_amount,
                    )

                await ctx.send(msg)
        except Exception as e:
            self.log.error(ctx.message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())

    @commands.command(name="invite", aliases=["inv", "join"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def invite(self, ctx, channel: typing.Optional[str] = None) -> None:
        _method = inspect.stack()[1][3]
        try:
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(
                    ctx.message.channel.name,
                    f"{self._module}.{self._class}.{_method}",
                    f"I am not in one of the required channels. {','.join(self.settings.bot_restricted_channels)}",
                )
                return

            if (
                channel is not None
                and channel != ""
                and self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT)
            ):
                channel = utils.clean_channel_name(channel)
                self.log.debug(
                    ctx.message.channel.name,
                    f"{self._module}.{self._class}.{_method}",
                    f"USER IS BOT OR BOT OWNER. CHANNEL: {channel}",
                )

            if channel is None or channel == "":
                channel = utils.clean_channel_name(ctx.message.author.name)


            # check if we know who this user is in discord.
            discord_id = self.db.get_discord_id_for_twitch_username(channel)
            if discord_id is None:
                await ctx.reply(
                    f"{ctx.message.author.mention}, I was unable to find a discord id for {channel}. Try running `!taco link` first."
                )
                return
            # we know who they are. add the channel to the database for channels to join.
            self.db.add_bot_to_channel(channel)
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{self._class}.{_method}",
                f"Added channel {channel} to channel list and joined channel.",
            )
            await self.bot.join_channels([f"#{channel}"])
            await ctx.reply(
                f"{ctx.message.author.mention}, I have added @{channel} to the channel list and joined the channel."
            )
            await self.tacos_log.give_user_tacos(
                fromUser=utils.clean_channel_name(self.bot.nick),
                toUser=channel,
                reason=f"Inviting @ourtacobot to their channel.",
                give_type=tacotypes.TacoTypes.TWITCH_BOT_INVITE,
                amount=5,
            )
        except ValueError as e:
            await ctx.reply(f"{ctx.message.author.mention}, {e}")
        except Exception as e:
            self.log.error(
                ctx.message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )

    @commands.command(name="leave", aliases=["part", "remove"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def leave(self, ctx, channel: typing.Optional[str] = None) -> None:
        _method = inspect.stack()[1][3]
        try:
            # only allowed in restricted channels
            # if ctx.message.channel.name not in self.settings.bot_restricted_channels:
            #     return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(
                    ctx.message.channel.name,
                    f"{self._module}.{self._class}.{_method}",
                    f"I am not in one of the required channels. {','.join(self.settings.bot_restricted_channels)}",
                )
                return

            if (
                channel is not None
                and channel != ""
                and self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT)
            ):
                channel = utils.clean_channel_name(channel)
                self.log.debug(
                    ctx.message.channel.name,
                    f"{self._module}.{self._class}.{_method}",
                    f"USER IS BOT OR BOT OWNER. CHANNEL: {channel}",
                )

            if channel is None or channel == "":
                channel = utils.clean_channel_name(ctx.message.author.name)

            # check if we know who this user is in discord.
            discord_id = self.db.get_discord_id_for_twitch_username(channel)
            if discord_id is None:
                await ctx.reply(
                    f"{ctx.message.author.mention}, I was unable to find {channel} discord id. Try running `!taco link` first."
                )
                return
            # we know who they are. add the channel to the database for channels to join.
            self.db.remove_bot_from_channel(channel)
            self.log.debug(
                ctx.message.channel.name,
                f"{self._module}.{self._class}.{_method}",
                f"Removed channel {channel} from the channel list and left the channel.",
            )
            # this currently doesn't work.
            # should be in future update of twitchio.
            # await self.bot.part_channels([f"#{channel}"])
            # workaround:
            await self.bot._connection.send(f"PART #{channel}\r\n")
            await ctx.reply(
                f"{ctx.message.author.mention}, I have removed the channel @{channel} from the list and left the channel."
            )
        except ValueError as e:
            await ctx.reply(f"{ctx.message.author.mention}, {e}")
        except Exception as e:
            self.log.error(
                ctx.message.channel.name, f"{self._module}.{self._class}.{_method}", str(e), traceback.format_exc()
            )

    async def cog_command_error(self, ctx: commands.core.Context, error: Exception):
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(str(error))
        else:
            await ctx.send(f"Error: {error}")

    def get_tacos_settings(self) -> dict:
        cog_settings = self.settings.get_settings(self.db, "tacos")
        if not cog_settings:
            raise Exception(f"No tacos settings found for guild {self.settings.discord_guild_id}")
        return cog_settings


def prepare(bot) -> None:
    bot.add_cog(TacoInviteCog(bot))
