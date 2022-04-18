from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
from .lib import mongo
from .lib import settings
from .lib import utils

### DiscordAccountLinkCog ###
# A way to link a twitch account to a discord account
# If a code is supplied, it will be used to link the discord account to the twitch account
# If no code is supplied, it will generate a code and then can be used in discord to link the discord account to the twitch account

class DiscordAccountLinkCog(commands.Cog):

    def __init__(self):
        print(f"loading DiscordAccountLink Cog")
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()

    @commands.command(name='link')
    async def link(self, ctx, code: str = None):
        if ctx.message.echo:
            return
        if code:
            # lookup code in db
            # if code is valid, link discord account to twitch account
            # if code is invalid, return error
            # if code is already linked, return error
            pass
        else:
            # generate code
            # save code to db
            # send code to user in chat
            pass
        # if code:
        #     invite_data = self.db.get_invite_for_code(code)
        #     if invite_data:
        #         await ctx.send(f"{invite_data['info']['url']}")
        #     else:
        #         await ctx.send(f"No invite found for code {code}")
        # else:
        #     await ctx.send(f"Please provide a code")

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
    bot.add_cog(DiscordAccountLinkCog())
