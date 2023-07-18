import re
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
from .lib.sa_types import StreamAvatarTypes

class StreamAvatars(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        _method = inspect.stack()[0][3]
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)
        self.TACO_AMOUNT = 5
        self.event_name = "stream_avatars"
        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]
        self.set_commands = ["set", "update"]

        self.default_settings = {
          "enabled": True,
          "action_message": r"^(?P<challenger>@?[a-zA-Z0-9-_]+) Has Challenged (?P<opponent>@?[a-zA-Z0-9-_]+) To A Duel with a buyin of (?P<buyin>\d{1,}). Type \!accept or \!decline within \d{1,} seconds$",
          "winner_message": r"^Congratulations to (?P<winner>@?[a-zA-Z0-9-_]+) for winning the duel! \+(?P<buyin>\d{1,})$",
          "accept_message": r"^(?P<opponent>@?[a-zA-Z0-9-_]+) has accepted the duel against (?P<challenger>@?[a-zA-Z0-9-_]+)!$",
          "decline_message": r"^(?P<opponent>@?[a-zA-Z0-9-_]+) has declined the duel$",
        }

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", f"{self._module}.{_method}", "Initialized")

    async def end_duel(self, message, duel, winner: str) -> None:
        _method = inspect.stack()[0][3]
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            if not duel or winner is None or winner == "":
                return

            winner = utils.clean_channel_name(winner)
            opponent = utils.clean_channel_name(duel.opponent)
            challenger = utils.clean_channel_name(duel.challenger)
            buyin = duel.count


            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            game_settings = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                self.log.debug(channel, f"{self._module}.{_method}", "Event disabled")
                return

            self.db.track_twitch_stream_avatar_duel(
                channel=channel,
                challenger=challenger,
                opponent=opponent,
                count=buyin,
                winner=winner,
                type=StreamAvatarTypes.COMPLETE
            )


            # from here we only care if the opponent is the bot
            if opponent != utils.clean_channel_name(self.bot.nick):
                self.log.debug(channel, f"{self._module}.{_method}", "Opponent is not the bot")
                return

            if winner == utils.clean_channel_name(self.bot.nick):
                # winner is the bot, so just exit as we wont give the bot tacos
                return

            # if the user is a known taco user, give tacos
            if not self.permissions_helper.has_linked_account(challenger) or buyin <= 0:
                # not linked account, or no buyin, so no tacos to give
                return

            # give the winner tacos
            await self.tacos_log.give_user_tacos(
                fromUser=channel,
                toUser=winner,
                reason=f"Winning a Stream Avatars Duel against {opponent} in {channel}'s channel",
                give_type=tacotypes.TacoTypes.TWITCH_STREAM_AVATARS,
                amount=self.TACO_AMOUNT
            )

            self.db.track_twitch_stream_avatar_duel(
                channel=channel,
                challenger=challenger,
                opponent=opponent,
                count=buyin,
                winner=winner,
                type=StreamAvatarTypes.COMPLETE
            )
        except Exception as e:
            raise e


    async def start_duel(self, message, opponent: str, challenger: str, buyin: int) -> None:
        _method = inspect.stack()[0][3]
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            game_settings = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                self.log.debug(channel, f"{self._module}.{_method}", "Event disabled")
                return

            self.db.track_twitch_stream_avatar_duel(
                channel=channel,
                challenger=challenger,
                opponent=opponent,
                count=buyin,
                winner=None,
                type=StreamAvatarTypes.REQUESTED
            )

            # if the buyin is not a positive number, use 0
            if buyin < 0:
                buyin = 0

            # from here we only care if the opponent is the bot
            if opponent != utils.clean_channel_name(self.bot.nick):
                self.log.debug(channel, f"{self._module}.{_method}", "Challenged is not the bot")
                return

            # if the user is not a known taco user, decline the duel if there is a buyin
            if not self.permissions_helper.has_linked_account(challenger) and buyin > 0:
                await message.channel.send("!decline")
                # will be tracked by the !decline listener
                return

            else:
                await message.channel.send("!accept")
                # will be tracked by the !accept listener
                return
        except Exception as e:
            raise e

    async def duel_accepted(self, message, duel) -> None:
        _method = inspect.stack()[0][3]
        try:
            self.db.track_twitch_stream_avatar_duel(
                channel=duel.channel,
                challenger=duel.challenger,
                opponent=duel.opponent,
                count=duel.count,
                winner=None,
                type=StreamAvatarTypes.ACCEPTED
            )
        except Exception as e:
            raise e

    async def duel_declined(self, message, duel) -> None:
        _method = inspect.stack()[0][3]
        try:
            self.db.track_twitch_stream_avatar_duel(
                channel=duel.channel,
                challenger=duel.challenger,
                opponent=duel.opponent,
                count=duel.count,
                winner=None,
                type=StreamAvatarTypes.DECLINED
            )
        except Exception as e:
            raise e

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        _method = inspect.stack()[0][3]
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            if self.event_name not in channel_settings:
                channel_settings[self.event_name] = self.default_settings
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            game_settings = channel_settings.get(self.event_name, self.default_settings)
            if not game_settings.get("enabled", True):
                self.log.debug(channel, f"{self._module}.{_method}", "Event disabled")
                return

            # make sure the settings are in the channel settings for each property
            action_pattern = game_settings.get("action_message", self.default_settings['action_message'])
            if "action_message" not in game_settings:
                channel_settings[self.event_name]["action_message"] = self.default_settings['action_message']
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            winner_pattern = game_settings.get("winner_message", self.default_settings['winner_message'])
            if "winner_message" not in game_settings:
                channel_settings[self.event_name]["winner_message"] = self.default_settings['winner_message']
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            accept_pattern = game_settings.get("accept_message", self.default_settings['accept_message'])
            if "accept_message" not in game_settings:
                channel_settings[self.event_name]["accept_message"] = self.default_settings['accept_message']
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            decline_pattern = game_settings.get("decline_message", self.default_settings['decline_message'])
            if "decline_message" not in game_settings:
                channel_settings[self.event_name]["decline_message"] = self.default_settings['decline_message']
                self.settings.set_channel_settings(self.db, channel, channel_settings)

            start_match_regex = re.compile(action_pattern, re.IGNORECASE| re.MULTILINE )
            winner_match_regex = re.compile(winner_pattern, re.IGNORECASE| re.MULTILINE )
            accept_match_regex = re.compile(accept_pattern, re.IGNORECASE| re.MULTILINE )
            decline_match_regex = re.compile(decline_pattern, re.IGNORECASE| re.MULTILINE )



            if sender != channel:
                return
            # if message.content matches epic regex
            start_duel_match = start_match_regex.match(message.content)
            accept_match = accept_match_regex.match(message.content)
            decline_match = decline_match_regex.match(message.content)
            winner_match = winner_match_regex.match(message.content)

            if start_match_regex.match(message.content):
                self.log.debug(channel, f"{self._module}.{_method}", "Message matched to start duel")
                opponent = start_duel_match.group("opponent")
                challenger = start_duel_match.group("challenger")
                buyin = int(start_duel_match.group("buyin"))
                await self.start_duel(message, opponent, challenger, buyin)
                return
            elif accept_match:
                opponent = accept_match.group("opponent")
                challenger = accept_match.group("challenger")
                duel = self.db.get_twitch_stream_avatar_duel_from_challenger_opponent(
                    channel=channel,
                    challenger=challenger,
                    opponent=opponent,
                    type=StreamAvatarTypes.REQUESTED)
                if duel is None:
                    self.log.debug(channel, f"{self._module}.{_method}", f"Could not find duel: {challenger} vs {opponent}")
                    return
                await self.duel_accepted(message, duel)
            elif decline_match:
                opponent = decline_match.group("opponent")
                duel = self.db.get_twitch_stream_avatar_duel_from_user(channel=channel, user=opponent, type=StreamAvatarTypes.REQUESTED)
                if duel is None:
                    self.log.debug(channel, f"{self._module}.{_method}", f"Could not find duel for opponent: {opponent}")
                    return

                await self.duel_declined(message, duel)
            elif winner_match:
                self.log.debug(channel, f"{self._module}.{_method}", "Message matched for winner")
                winner = winner_match.group("winner")
                buyin = int(winner_match.group("buyin"))

                duel = self.db.get_twitch_stream_avatar_duel_from_user(channel=channel, user=winner, type=StreamAvatarTypes.ACCEPTED)
                if duel is None:
                    self.log.debug(channel, f"{self._module}.{_method}", f"Could not find duel for winner: {winner}")
                    return

                challenger = duel.challenger
                opponent = duel.opponent
                buyin = duel.count

                self.log.debug(channel, f"{self._module}.{_method}", f"Found duel between: {duel.challenger} and {duel.opponent} with a buyin of {duel.count}")

                await self.end_duel(
                    message=message,
                    duel=duel,
                    winner=winner
                )

                return
            else:
                return

        except Exception as e:
            self.log.error(message.channel.name, f"{self._module}.{_method}", str(e), traceback.format_exc())
def prepare(bot) -> None:
    bot.add_cog(StreamAvatars(bot))
