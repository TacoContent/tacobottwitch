from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect

from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import loglevel
from .lib import logger
from .lib import permissions
from .lib import command_helper
from .lib import tacos_log as tacos_log
from .lib import tacotypes

class TacoInviteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
        self.log.debug("NONE", "invite.__init__", "Initialized")

    @commands.command(name="discord", aliases=["taco"])
    @commands.cooldown(1, 30, commands.Bucket.channel)
    async def discord(self, ctx):
        _method = inspect.stack()[1][3]

        try:
            if ctx.message.echo:
                return

            invite_data = self.db.get_invite_for_user(ctx.message.channel.name)
            if invite_data is None:
                invite_data = self.db.get_any_invite()

            if invite_data is None:
                await ctx.send(f"I was unable to find an invite code to use for {ctx.message.channel.name}. Please create an invite in discord and try again.")
                return
            else:
                url = invite_data["info"]["url"]
                msg = utils.str_replace(self.invite_message, url=url, team=self.settings.twitch_team_name)
                await ctx.send(msg)
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    @commands.command(name="invite", aliases=["inv", "join"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def invite(self, ctx, channel: str = None):
        _method = inspect.stack()[1][3]
        try:
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"I am not in one of the required channels. {','.join(self.settings.bot_restricted_channels)}")
                return

            if ctx.message.echo:
                return

            channel = ctx.message.author.name
            if channel is not None and channel != "" and self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT_OWNER):
                channel = channel.lower().strip().replace("@", "")

            if channel is None or channel == "":
                channel = ctx.message.author.name


            # check if we know who this user is in discord.
            discord_id = self.db.get_discord_id_for_twitch_username(channel)
            if discord_id is None:
                await ctx.reply(f"{ctx.message.author.mention}, I was unable to find a discord id for {channel}. Try running `!taco link` first.")
                return
            # we know who they are. add the channel to the database for channels to join.
            self.db.add_bot_to_channel(channel)
            self.log.debug(ctx.message.channel.name, _method, f"Added channel {channel} to channel list and joined channel.")
            await self.bot.join_channels([f"#{channel}"])
            await ctx.reply(f"{ctx.message.author.mention}, I have added {channel} to the channel list and joined the channel.")
            await self.tacos_log.give_user_tacos(ctx.message.channel.name, channel, "Inviting @ourtacobot to their channel.", tacos_log.TacoType.CUSTOM, 5)
        except ValueError as e:
            await ctx.reply(f"{ctx.message.author.mention}, {e}")
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    @commands.command(name="leave", aliases=["part", "remove"])
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def leave(self, ctx, channel: str = None):
        _method = inspect.stack()[1][3]
        try:
            # only allowed in restricted channels
            # if ctx.message.channel.name not in self.settings.bot_restricted_channels:
            #     return
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"I am not in one of the required channels. {','.join(self.settings.bot_restricted_channels)}")
                return

            if ctx.message.echo:
                return

            channel = ctx.message.author.name
            if channel is not None and channel != "" and self.permissions_helper.has_permission(ctx.message.author.name, permissions.PermissionLevel.BOT_OWNER):
                channel = channel.lower().strip().replace("@", "")

            if channel is None or channel == "":
                channel = ctx.message.author.name

            # check if we know who this user is in discord.
            discord_id = self.db.get_discord_id_for_twitch_username(channel)
            if discord_id is None:
                await ctx.reply(f"{ctx.message.author.mention}, I was unable to find {channel} discord id. Try running `!taco link` first.")
                return
            # we know who they are. add the channel to the database for channels to join.
            self.db.remove_bot_from_channel(channel)
            self.log.debug(ctx.message.channel.name, _method, f"Removed channel {channel} from the channel list and left the channel.")
            # this currently doesn't work.
            # should be in future update of twitchio.
            # await self.bot.part_channels([f"#{channel}"])
            # workaround:
            await self.bot._connection.send(f"PART #{channel}\r\n")
            await ctx.reply(f"{ctx.message.author.mention}, I have removed the channel {channel} from the list and left the channel.")
        except ValueError as e:
            await ctx.reply(f"{ctx.message.author.mention}, {e}")
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    @commands.Cog.event()
    async def event_raw_data(self, data):
        pass

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message):
        # is the message from the bot?
        if message.echo:
            return

        pass

    async def cog_command_error(self, ctx: commands.core.Context, error: Exception):
        print(f"Error: {str(error)}")
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(str(error))
        else:
            await ctx.send(f"Error: {error}")


def prepare(bot):
    bot.add_cog(TacoInviteCog(bot))
