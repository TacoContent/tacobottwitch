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
class TacoInviteCog(commands.Cog):

    def __init__(self):
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)


        self.invite_message = "🌮🌮🌮 Join an amazing discord community that I am passionate about. TACO - The Alliance Collective Order - Tacos Aren't Just For Tuesday 🌮🌮🌮 -> Discord: {{url}} -> Twitch Team: https://twitch.tv/team/{{team}} -> Twitter: https://www.twitter.com/OurTaco"
        self.log.debug("NONE", "invite.__init__", "Initialized")

    @commands.command(name='taco')
    @commands.cooldown(1, 30, commands.Bucket.channel)
    async def taco(self, ctx):
        _method = inspect.stack()[1][3]

        try:
            if ctx.message.echo:
                return

            invite_data = self.db.get_invite_for_user(ctx.message.channel.name)
            if invite_data is None:
                invite_data = self.db.get_any_invite()

            if invite_data is None:
                await ctx.send(f"I was unable to find invite code for {ctx.message.channel.name}.")
                return
            else:
                url = invite_data['info']['url']
                msg = utils.str_replace(self.invite_message, url=url, team=self.settings.twitch_team_name)
                await ctx.send(msg)
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
    bot.add_cog(TacoInviteCog())
