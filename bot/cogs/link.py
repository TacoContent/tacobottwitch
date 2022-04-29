import imp
from twitchio.ext import commands
import twitchio
import os
import traceback
import inspect
import sys
import json
from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import permissions
from .lib import loglevel
from .lib import logger

# from .lib import permissions

### DiscordAccountLinkCog ###
# A way to link a twitch account to a discord account
# If a code is supplied, it will be used to link the discord account to the twitch account
# If no code is supplied, it will generate a code and then can be used in discord to link the discord account to the twitch account


class DiscordAccountLinkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG
            
        self.permissions_helper = permissions.Permissions()

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", "account_link.__init__", "Initialized")
    @commands.command(name="update")
    # @permissions.has_permission(permission=permissions.Permssions.EVERYONE)
    @commands.cooldown(1, 30, commands.Bucket.channel)
    # @commands.restrict_channels(channels=["ourtacobot", "ourtaco"])
    async def update(self, ctx: commands.Context):
        _method = inspect.stack()[1][3]
        try:
            if not self.permissions_helper.in_command_restricted_channel(ctx):
                self.log.debug(ctx.message.channel.name, _method, f"I am not in one of the required channels. {','.join(self.settings.bot_restricted_channels)}")
                return

            if channel is not None and channel != "" and self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.BOT):
                channel = utils.clean_channel_name(channel)
                self.log.debug(ctx.message.channel.name, _method, f"USER IS BOT OR BOT OWNER. CHANNEL: {channel}")

            if channel is None or channel == "":
                channel = utils.clean_channel_name(ctx.message.author.name)

        except ValueError as e:
            await ctx.reply(f"{ctx.message.author.mention}, {e}")
        except Exception as e:
            self.log.error(ctx.message.channel.name, _method, str(e), traceback.format_exc())

    @commands.command(name="link")
    # @permissions.has_permission(permission=permissions.Permssions.EVERYONE)
    async def link(self, ctx, code: str = None):
        _method = inspect.stack()[1][3]
        if code:
            try:
                result = self.db.link_twitch_to_discord_from_code(utils.clean_channel_name(ctx.message.author.name), code)
                if result:
                    await ctx.reply(
                        f"{ctx.message.author.mention}, I used the code {code} to link your discord account to your twitch account. Thank you!"
                    )
                else:
                    await ctx.reply(
                        f"{ctx.message.author.mention}, I couldn't find a verification code with that value. Please try again."
                    )
            except ValueError as ver:
                await ctx.reply(f"{ctx.message.author.mention}, {ver}")
        else:
            try:
                # generate code
                invite_data = self.db.get_invite_for_user(utils.clean_channel_name(ctx.message.channel.name))
                if invite_data:
                    self.log.debug(
                        ctx.message.channel.name,
                        "account_link.link",
                        f"Found invite data for {ctx.message.channel.name}",
                    )
                    discord_invite = invite_data["info"]["url"]
                else:
                    invite_data = self.db.get_any_invite()
                    if invite_data:
                        self.log.debug(
                            ctx.message.channel.name,
                            "account_link.link",
                            f"Found random invite data for {ctx.message.channel.name}",
                        )
                        discord_invite = invite_data["info"]["url"]

                code = utils.get_random_string(length=6)
                # save code to db
                result = self.db.set_twitch_discord_link_code(utils.clean_channel_name(ctx.message.author.name), code)
                if result:
                    # send code to user in chat
                    await ctx.reply(
                        f"{ctx.message.author.mention}, Please use this code in discord to link your discord and twitch accounts -> `.taco link {code}` <- {discord_invite}"
                    )
                else:
                    await ctx.reply(f"{ctx.message.author.mention}, I couldn't save your code. Please try again.")
            except ValueError as ver:
                await ctx.reply(f"{ctx.message.author.mention}, {ver}")

    async def cog_check(self, ctx: commands.core.Context) -> bool:
        return True

    # @commands.Cog.event("cog_command_error")
    # this is not triggered...
    async def cog_command_error(self, ctx: commands.Context, error: Exception):
        print(f"Error: {str(error)}")
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(str(error))
        else:
            await ctx.send(f"Error: {error}")


def prepare(bot):
    bot.add_cog(DiscordAccountLinkCog(bot))
