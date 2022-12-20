from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
from .lib import mongo
from .lib import settings


class MessageLoggingCog(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        pass

    @commands.Cog.event()
    async def event_raw_data(self, data) -> None:
        pass

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        # is the message from the bot?
        if message.echo or message.author is None or message.channel is None:
            return

        print(f"{message.channel.name} -> {json.dumps(message.author.badges)} {message.author.name} -> {message.content}")

    @commands.Cog.event()
    async def event_ready(self) -> None:
        pass
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f"Logged in as | {self.bot.nick}")
        print(f"User id is | {self.bot.user_id}")

        # get the twitch channels to join from the database
        # channels = self.db.get_twitch_channels()


def prepare(bot) -> None:
    bot.add_cog(MessageLoggingCog(bot))
