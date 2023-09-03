import inspect
import os
import traceback
import typing

from bot.cogs.lib import logger, loglevel, mongo, settings
from twitchio.ext import commands

# https://twitchio.dev/en/latest/exts/commands.html#twitchio.ext.commands.Bot.load_module
class TacoBot(commands.Bot):
    def __init__(self) -> None:
        _method = inspect.stack()[0][3]
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]
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

        super().__init__(
            token=self.settings.twitch_oauth_token,
            prefix=self.get_prefixes,
            initial_channels=self.get_initial_channels,
            # client_secret=self.settings.twitch_client_secret,
            # client_id=self.settings.twitch_client_id,
        )
        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        # self.bot = commands.Bot(
        #     token=self.settings.twitch_oauth_token, prefix=self.get_prefixes, initial_channels=self.get_initial_channels
        # )
        # self.esclient = eventsub.EventSubClient(
        #     client=self,
        #     callback_route=self.settings.eventsub_callback_url,
        #     webhook_secret=self.settings.eventsub_secret,
        # )
        # get a list of all the cogs in the cogs directory
        cogs = [
            f"bot.cogs.{os.path.splitext(f)[0]}"
            for f in os.listdir("bot/cogs")
            if f.endswith(".py") and not f.startswith("_")
        ]

        # load all the cogs
        for extension in cogs:
            try:
                # self.bot.load_module(extension)
                self.load_module(extension)
            except Exception as e:
                self.log.error(
                    "NONE",
                    f"{self._module}.{self._class}.{_method}",
                    f"Failed to load extension {extension}: {e}",
                    traceback.format_exc(),
                )
        self.log.debug("NONE", f"{self._module}.{_method}", "Starting bot")
        self.run()

    # async def __ainit__(self) -> None:
    #     self.loop.create_task(self.esclient.listen(port=4000))

    #     # get all the channels that we are monitoring and create the eventsub subscriptions
    #     channels = []
    #     if self.settings.IS_DEBUG:
    #         channels = self.settings.default_channels
    #     else:
    #         channels = self.db.get_bot_twitch_channels()

    #     for channel in channels:
    #         try:
    #             self.log.debug("NONE", "tacobot.__ainit__", f"subscribing to follow event for channel: {channel}")
    #             await self.esclient.subscribe_channel_follows_v2(broadcaster=utils.clean_channel_name(channel), moderator=self.user_id)
    #         except twitchio.HTTPException as e:
    #             self.log.error("NONE", "tacobot.__ainit__", f"failed to subscribe to follow event for channel: {channel} -> {str(e)}", traceback.format_exc())
    #             pass

    def get_initial_channels(self) -> typing.Optional[list[str]]:
        _method = inspect.stack()[0][3]
        try:
            if self.settings.IS_DEBUG:
                self.log.debug("NONE", f"{self._module}.{_method}", "debug mode, joining default channels")
                return self.settings.default_channels

            channels = self.db.get_bot_twitch_channels()
            if not channels:
                self.log.debug(
                    "NONE", f"{self._module}.{_method}", "no channels found in database, joining default channels"
                )
                return self.settings.default_channels

            self.log.debug("NONE", f"{self._module}.{_method}", f"joining channels: {', '.join(channels)}")

            return channels
        except Exception as e:
            self.log.error("NONE", f"{self._module}.{_method}", str(e), traceback.format_exc())
            return self.settings.default_channels

    async def get_prefixes(self, client, message) -> list:
        _method = inspect.stack()[0][3]
        try:
            # default prefixes
            prefixes = self.settings.bot_prefixes
            return prefixes
        except Exception as e:
            self.log.error("NONE", f"{self._module}.{_method}", str(e), traceback.format_exc())
            return self.settings.bot_prefixes
