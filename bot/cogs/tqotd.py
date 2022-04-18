from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
from .lib import mongo
from .lib import settings
from .lib import utils

class TacoQuestionOfTheDayCog(commands.Cog):
    def __init__(self):
        print(f"loading TacoQuestionOfTheDayCog")
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()

    @commands.command(name='tqotd')
    async def tqotd(self, ctx):
        if ctx.message.echo:
            return
        question = self.db.get_tqotd()
        if question:
            invite_data = self.db.get_invite_for_user(ctx.message.channel.name)
            if invite_data:
                await ctx.send(f"TACO Question of the Day: {question} -> Join the discussion: {invite_data['info']['url']}")
            else:
                await ctx.send(f"TACO Question of the Day: {question}")
        else:
            await ctx.send(f"No TACO Question of the Day found. Check back later.")

def prepare(bot):
    bot.add_cog(TacoQuestionOfTheDayCog())
