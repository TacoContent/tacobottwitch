from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
from .cogs.lib import mongo
from .cogs.lib import settings
from .cogs.lib import logger
from .cogs.lib import loglevel

# https://twitchio.dev/en/latest/exts/commands.html#twitchio.ext.commands.Bot.load_module
class TacoBot():

    def __init__(self):
        self.settings = settings.Settings()

        if not self.settings.twitch_oauth_token:
            raise Exception("TWITCH_OAUTH_TOKEN is not set")
        if not self.settings.twitch_client_secret:
            raise Exception("TWITCH_CLIENT_SECRET is not set")

        self.db = mongo.MongoDatabase()

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.log.debug("NONE", "tacobot.__init__", "Initialized")

        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        self.bot = commands.Bot(token=self.settings.twitch_oauth_token, prefix=self.get_prefixes, initial_channels=self.get_initial_channels)

        # get a list of all the cogs in the cogs directory
        cogs = [ f"bot.cogs.{os.path.splitext(f)[0]}" for f in os.listdir("bot/cogs") if f.endswith(".py") and not f.startswith("_") ]
        # load all the cogs
        for extension in cogs:
            try:
                self.bot.load_module(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()
        # print(f"starting bot")
        self.log.debug("NONE", "tacobot.__init__", "Starting bot")

        self.bot.run()

    def get_initial_channels(self):
        try:
            channels = self.db.get_bot_twitch_channels()
            self.log.debug("NONE", "tacobot.get_initial_channels", f"joining channels: {', '.join(channels)}")

            return channels
        except Exception as e:
            self.log.error("NONE", "tacobot.get_initial_channels", str(e), traceback.format_exc())
            return self.settings.default_channels

    async def get_prefixes(self, client, message):
        try:
            # default prefixes
            prefixes = self.settings.bot_prefixes
            return prefixes
        except Exception as e:
            self.log.error("NONE", "tacobot.get_prefixes", str(e), traceback.format_exc())
