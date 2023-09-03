import datetime
import inspect
import os
import random
import sys
import traceback
import typing

from bot.cogs.lib import loglevel, settings, utils
from bot.cogs.lib.sa_types import StreamAvatarTypes
from bot.cogs.lib.colors import Colors
from bson.objectid import ObjectId
from pymongo import MongoClient


class MongoDatabase:
    def __init__(self) -> None:
        self._class = self.__class__.__name__
        # get the file name without the extension and without the directory
        self._module = os.path.basename(__file__)[:-3]

        self.client = None
        self.connection = None
        self.settings = settings.Settings()

    def log(
        self,
        level: loglevel.LogLevel,
        method: str,
        message: str,
        stackTrace: typing.Optional[str] = None,
        channel: typing.Optional[str] = None,
    ) -> None:
        _method = inspect.stack()[0][3]
        if channel is None:
            channel = str(loglevel.EmptyChannel())

        color = Colors.get_color(level)
        m_level = Colors.colorize(color, f"[{level.name}]", bold=True)
        m_method = Colors.colorize(Colors.HEADER, f"[{method}]", bold=True)
        m_channel = Colors.colorize(Colors.OKGREEN, f"[{channel}]", bold=True)
        m_message = f"{Colors.colorize(color, message)}"
        stdoe = sys.stdout if level < loglevel.LogLevel.ERROR else sys.stderr

        str_out = f"{m_level} {m_method} {m_channel} {m_message}"

        print(str_out, file=stdoe)
        if stackTrace:
            print(Colors.colorize(color, stackTrace), file=stdoe)
        try:
            if level >= loglevel.LogLevel.INFO:
                self.insert_log(channel=channel, level=level, method=method, message=message, stackTrace=stackTrace)
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.PRINT,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"Unable to log to database: {ex}",
                stackTrace=traceback.format_exc(),
                channel=channel,
            )

    def open(self) -> None:
        if not self.settings.db_url:
            raise ValueError("MONGODB_URL is not set")
        self.client = MongoClient(self.settings.db_url)
        self.connection = self.client.tacobot

    def close(self) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.connection = None
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"Unable to close connection: {ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def insert_log(
        self, channel: str, level: loglevel.LogLevel, method: str, message: str, stackTrace: typing.Optional[str] = None
    ) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            payload = {
                "channel: ": utils.clean_channel_name(channel),
                "guild_id": self.settings.discord_guild_id,
                "timestamp": utils.get_timestamp(),
                "level": level.name,
                "method": method,
                "message": message,
                "stack_trace": stackTrace,
            }
            self.connection.logs.insert_one(payload)
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.PRINT,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=channel,
            )

    def clear_log(self, channel: str) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            channel = utils.clean_channel_name(channel)
            self.connection.logs.delete_many({"channel": channel})
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=channel,
            )

    def get_channel_settings(self, channel: str) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            channel = utils.clean_channel_name(channel)
            result = self.connection.twitch_channel_settings.find_one(
                {"guild_id": self.settings.discord_guild_id, "channel": channel}
            )
            if result:
                return result
            else:
                return None
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=channel,
            )
            return None

    def set_channel_settings(self, channel: str, settings: dict) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            channel = utils.clean_channel_name(channel)

            self.connection.twitch_channel_settings.update_one(
                {"guild_id": self.settings.discord_guild_id, "channel": channel},
                {"$set": {"settings": settings}},
                upsert=True,
            )
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.FATAL,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=channel,
            )
            raise ex

    def get_settings(self, name: str) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            settings = self.connection.settings.find_one({"guild_id": self.settings.discord_guild_id, "name": name})
            # explicitly return None if no settings are found
            if settings is None:
                return None
            # return the settings object
            return settings["settings"]
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def get_channels(self) -> typing.Optional[typing.List[str]]:
        return self.get_bot_twitch_channels()

    def get_bot_twitch_channels(self) -> typing.Optional[typing.List[str]]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            result = self.connection.twitch_channels.find({"guild_id": self.settings.discord_guild_id})
            if result:
                channels = [f"#{utils.clean_channel_name(x['channel'])}" for x in result]
                [
                    channels.append(f"#{utils.clean_channel_name(x)}")
                    for x in self.settings.default_channels
                    if f"#{utils.clean_channel_name(x)}" not in channels
                ]
                return channels
            else:
                self.log(
                    level=loglevel.LogLevel.WARNING,
                    method=f"{self._module}.{self._class}.{_method}",
                    message="Unable to find channels for bot",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
                return self.settings.default_channels
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message="Unable to find channels for bot",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def add_bot_to_channel(self, twitch_channel) -> bool:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            twitch_channel = utils.clean_channel_name(twitch_channel)
            result = self.connection.twitch_channels.find_one(
                {"guild_id": self.settings.discord_guild_id, "channel": twitch_channel}
            )
            if not result:
                timestamp = utils.to_timestamp(datetime.datetime.utcnow())
                payload = {
                    "guild_id": self.settings.discord_guild_id,
                    "channel": twitch_channel,
                    "timestamp": timestamp,
                }
                self.connection.twitch_channels.insert_one(payload)
                return True
            else:
                raise ValueError(f"Twitch channel {twitch_channel} already added")
        except ValueError as ve:
            self.log(
                level=loglevel.LogLevel.WARNING,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ve}",
                stackTrace=traceback.format_exc(),
                channel=twitch_channel,
            )
            raise ve
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.FATAL,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=twitch_channel,
            )
            raise ex

    def remove_bot_from_channel(self, twitch_channel) -> bool:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            twitch_channel = utils.clean_channel_name(twitch_channel)
            result = self.connection.twitch_channels.delete_one(
                {"guild_id": self.settings.discord_guild_id, "channel": twitch_channel}
            )
            if result.deleted_count == 1:
                return True
            else:
                raise ValueError(f"I was unable to leave channel {twitch_channel}, as I am not in it.")
        except ValueError as ve:
            self.log(
                loglevel.LogLevel.WARNING, f"{self._module}.{self._class}.{_method}", f"{ve}", traceback.format_exc()
            )
            raise ve
        except Exception as ex:
            self.log(
                loglevel.LogLevel.FATAL,
                f"{self._module}.{self._class}.{_method}",
                f"{ex}",
                traceback.format_exc(),
                channel=twitch_channel,
            )
            raise ex

    def get_any_invite(self) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            # get the count of all invites
            all_invites = list(self.connection.invite_codes.find({}))
            invite_count = len(all_invites)
            # get a random number between 0 and the count of invites
            rand_index = random.randint(0, invite_count)
            # get the invite at the random index and take 1 item
            result = self.connection.invite_codes.find({"guild_id": self.settings.discord_guild_id}).skip(rand_index)

            if result:
                return result[0]
            else:
                self.log(
                    loglevel.LogLevel.WARNING,
                    f"{self._module}.{self._class}.{_method}",
                    f"Unable to find invite code for bot",
                    traceback.format_exc(),
                    channel=None,
                )
                return None
        except Exception as ex:
            self.log(
                loglevel.LogLevel.WARNING,
                f"{self._module}.{self._class}.{_method}",
                f"{ex}",
                traceback.format_exc(),
                channel=None,
            )
            return None

    def get_invite_for_user(self, twitch_name: str) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            discord_user_id = self._get_discord_id(twitch_name)
            if discord_user_id:
                result = self.connection.invite_codes.find_one(
                    {"guild_id": self.settings.discord_guild_id, "info.inviter_id": discord_user_id}
                )
                if result:
                    return result
                else:
                    self.log(
                        level=loglevel.LogLevel.WARNING,
                        method=f"{self._module}.{self._class}.{_method}",
                        message=f"Unable to find invite code for twitch user {twitch_name}",
                        stackTrace=traceback.format_exc(),
                        channel=None,
                    )
                    return None
            else:
                return None
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def get_discord_id_for_twitch_username(self, username: str) -> typing.Optional[str]:
        _method = inspect.stack()[0][3]
        try:
            return self._get_discord_id(username)
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def get_tqotd(self) -> typing.Optional[str]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            date = datetime.datetime.utcnow().date()
            ts_date = datetime.datetime.combine(date, datetime.time.min)
            timestamp = utils.to_timestamp(ts_date)

            result = self.connection.tqotd.find_one(
                {"guild_id": self.settings.discord_guild_id, "timestamp": timestamp}
            )
            if result:
                return result["question"]
            else:
                # get yesterday's tqotd if we didnt find one for "today"
                date = date - datetime.timedelta(days=1)
                ts_date = datetime.datetime.combine(date, datetime.time.min)
                timestamp = utils.to_timestamp(ts_date)
                result = self.connection.tqotd.find_one(
                    {"guild_id": self.settings.discord_guild_id, "timestamp": timestamp}
                )
                if result:
                    return result["question"]
                return None
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def _get_discord_id(self, username: str) -> typing.Optional[str]:
        if self.connection is None:
            self.open()
        username = utils.clean_channel_name(username)
        result = self.connection.twitch_user.find_one({"twitch_name": username})
        if result:
            return result["user_id"]
        else:
            return None

    def set_twitch_discord_link_code(self, username: str, code: str) -> bool:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            username = utils.clean_channel_name(username)
            discord_user_id = self._get_discord_id(username)
            if not discord_user_id:
                payload = {"twitch_name": username, "link_code": code.strip()}
                self.connection.twitch_user.update_one({"twitch_name": username}, {"$set": payload}, upsert=True)
                return True
            else:
                raise ValueError(f"Twitch user {username} already linked")
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.FATAL,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            raise ex

    def link_twitch_to_discord_from_code(self, twitch_name: str, code: str) -> bool:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            twitch_name = utils.clean_channel_name(twitch_name)
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                result = self.connection.twitch_user.find_one({"link_code": code.strip()})
                if result:
                    payload = {
                        "twitch_name": twitch_name,
                        # "user_id": result["user_id"],
                        # "link_code": code.strip()
                    }
                    self.connection.twitch_user.update_one({"link_code": code.strip()}, {"$set": payload}, upsert=True)
                    return True
                else:
                    raise ValueError(f"Unable to find an entry for a user with link code: {code}")
            else:
                raise ValueError(f"Twitch user {twitch_name} already linked")
        except ValueError as ve:
            raise ve
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.FATAL,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            raise ex

    def get_top_tacos_leaderboard(self, limit: int = 10) -> typing.Optional[list]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            result = self.connection.tacos.aggregate(
                [
                    {
                        "$lookup": {
                            "from": "twitch_user",
                            "localField": "user_id",
                            "foreignField": "user_id",
                            "as": "user",
                        }
                    },
                    {"$unwind": "$user"},
                    {"$match": {"guild_id": self.settings.discord_guild_id}},
                    {"$sort": {"count": -1}},
                    {"$limit": limit},
                ]
            )

            if result:
                return list(result)
            else:
                return None
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def get_tacos_count(self, twitch_name: str) -> typing.Optional[int]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            twitch_name = utils.clean_channel_name(twitch_name)
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                return 0

            data = self.connection.tacos.find_one(
                {"guild_id": self.settings.discord_guild_id, "user_id": discord_user_id}
            )
            if data is None:
                self.log(
                    level=loglevel.LogLevel.DEBUG,
                    method=f"{self._module}.{self._class}.{_method}",
                    message=f"User {twitch_name}[{discord_user_id}] not in table",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
                return 0
            return data["count"]
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def add_tacos(self, twitch_name: str, count: int) -> typing.Optional[int]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            twitch_name = utils.clean_channel_name(twitch_name)
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                return 0

            user_tacos = self.get_tacos_count(twitch_name=twitch_name)
            if user_tacos is None:
                self.log(
                    level=loglevel.LogLevel.DEBUG,
                    method=f"{self._module}.{self._class}.{_method}",
                    message=f"User {twitch_name}[{discord_user_id}] not in table",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
                user_tacos = 0
            else:
                user_tacos = user_tacos or 0
                self.log(
                    level=loglevel.LogLevel.DEBUG,
                    method=f"{self._module}.{self._class}.{_method}",
                    message=f"User {twitch_name}[{discord_user_id}] has {user_tacos} tacos",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
            user_tacos += count
            self.log(
                level=loglevel.LogLevel.DEBUG,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"User {twitch_name}[{discord_user_id}] now has {user_tacos} taco",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            self.connection.tacos.update_one(
                {"guild_id": self.settings.discord_guild_id, "user_id": discord_user_id},
                {"$set": {"count": user_tacos}},
                upsert=True,
            )
            return user_tacos
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def remove_tacos(self, twitch_name: str, count: int) -> int:
        _method = inspect.stack()[0][3]
        try:
            if count < 0:
                self.log(
                    level=loglevel.LogLevel.DEBUG,
                    method=f"{self._module}.{self._class}.{_method}",
                    message=f"Count is fewer than 0.",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
                return 0
            if self.connection is None:
                self.open()
            twitch_name = utils.clean_channel_name(twitch_name)
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                return 0

            user_tacos = self.get_tacos_count(twitch_name=twitch_name)
            if user_tacos is None:
                self.log(
                    level=loglevel.LogLevel.DEBUG,
                    method=f"{self._module}.{self._class}.{_method}",
                    message=f"User {twitch_name}[{discord_user_id}] not in table.",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
                user_tacos = 0
            else:
                user_tacos = user_tacos or 0
                self.log(
                    level=loglevel.LogLevel.DEBUG,
                    method=f"{self._module}.{self._class}.{_method}",
                    message=f"User {twitch_name}[{discord_user_id}] has {user_tacos} tacos",
                    stackTrace=traceback.format_exc(),
                    channel=None,
                )
            user_tacos -= count
            if user_tacos < 0:
                user_tacos = 0
            self.log(
                level=loglevel.LogLevel.DEBUG,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"User {twitch_name}[{discord_user_id}] now has {user_tacos} tacos",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            self.connection.tacos.update_one(
                {"guild_id": self.settings.discord_guild_id, "user_id": discord_user_id},
                {"$set": {"count": user_tacos}},
                upsert=True,
            )
            return user_tacos
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def track_taco_gift(self, channel: str, user: str, amount: int, reason: typing.Optional[str] = None) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            channel = utils.clean_channel_name(channel)
            user = utils.clean_channel_name(user)
            from_discord_user_id = self._get_discord_id(channel)
            to_discord_user_id = self._get_discord_id(user)

            payload = {
                "guild_id": self.settings.discord_guild_id,
                "channel": channel,
                "from_user_id": from_discord_user_id,
                "twitch_name": user,
                "to_user_id": to_discord_user_id,
                "count": amount,
                "timestamp": utils.get_timestamp(),
                "reason": reason,
            }

            self.connection.twitch_tacos_gifts.insert_one(payload)
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def get_total_gifted_tacos(self, channel: str, timespan_seconds: int = 86400) -> int:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            timestamp = utils.to_timestamp(datetime.datetime.utcnow())
            channel = utils.clean_channel_name(channel)
            data = self.connection.taco_gifts.find(
                {
                    "guild_id": self.settings.discord_guild_id,
                    "channel": channel,
                    "timestamp": {"$gt": timestamp - timespan_seconds},
                }
            )
            if data is None:
                return 0
            # add up all the gifts from the count column
            total_gifts = 0
            for gift in data:
                total_gifts += gift["count"]
            return total_gifts
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return 0

    def get_total_gifted_tacos_to_user(self, channel: str, user: str, timespan_seconds: int = 86400) -> int:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            timestamp = utils.to_timestamp(datetime.datetime.utcnow())
            channel = utils.clean_channel_name(channel)
            user = utils.clean_channel_name(user)
            data = self.connection.taco_gifts.find(
                {
                    "guild_id": self.settings.discord_guild_id,
                    "channel": channel,
                    "twitch_name": user,
                    "timestamp": {"$gt": timestamp - timespan_seconds},
                }
            )

            if data is None:
                return 0
            # add up all the gifts from the count column
            total_gifts = 0
            for gift in data:
                total_gifts += gift["count"]
            return total_gifts
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return 0

    def track_user_message_in_chat(self, channel: str, user: str, message: str, timespan_seconds: int = 86400) -> bool:
        _method = inspect.stack()[0][3]
        # if the user has not messaged in the channel in the last timespan_seconds, add them to the database
        try:
            if self.connection is None:
                self.open()
            timestamp = utils.to_timestamp(datetime.datetime.utcnow())
            channel = utils.clean_channel_name(channel)
            user = utils.clean_channel_name(user)
            data = self.connection.twitch_first_message.find_one(
                {"guild_id": self.settings.discord_guild_id, "channel": channel, "twitch_name": user}
            )
            if data is not None:
                # if timestamp was more than 24 hours ago, add the user to the database
                if abs(data["timestamp"] - timestamp) > timespan_seconds:
                    payload = {
                        "guild_id": self.settings.discord_guild_id,
                        "channel": channel,
                        "twitch_name": user,
                        "timestamp": timestamp,
                        "message": message,
                    }
                    self.connection.twitch_first_message.update_one(
                        {"guild_id": self.settings.discord_guild_id, "channel": channel, "twitch_name": user},
                        {"$set": payload},
                    )
                    return True
                return False
            else:
                # they have never said anything...
                data = self.connection.twitch_first_message.insert_one(
                    {
                        "guild_id": self.settings.discord_guild_id,
                        "channel": channel,
                        "twitch_name": user,
                        "message": message,
                        "timestamp": timestamp,
                    }
                )
                return True
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return False

    def get_active_game_offer(self) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()

            # get the open offer:
            offer = self.connection.game_key_offers.find_one({"guild_id": self.settings.discord_guild_id})
            if offer:
                # get game data
                game_data = self.connection.game_keys.find_one({"_id": ObjectId(str(offer['game_key_id']))})
                if game_data:
                    return {"title": game_data['title']}
            else:
                return None
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def track_tacos_log(self, channel: str, user: str, count: int, type: str, reason: str):
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            date = datetime.datetime.utcnow()
            timestamp = utils.to_timestamp(date)
            channel = utils.clean_channel_name(channel)
            user = utils.clean_channel_name(user)

            from_discord_user_id = self._get_discord_id(channel)
            to_discord_user_id = self._get_discord_id(user)

            payload = {
                "guild_id": self.settings.discord_guild_id,
                "from_user_id": str(from_discord_user_id),
                "to_user_id": str(from_discord_user_id),
                "count": count,
                "type": type,
                "reason": reason,
                "timestamp": timestamp,
            }

            self.connection.tacos_log.insert_one(payload)
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def track_twitch_stream_avatar_duel(
        self,
        channel: str,
        challenger: typing.Optional[str],
        opponent: typing.Optional[str],
        count: typing.Optional[int],
        winner: typing.Optional[str],
        type: StreamAvatarTypes,
        ignore_closed: bool = False,
    ) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()
            date = datetime.datetime.utcnow()
            timestamp = utils.to_timestamp(date)
            channel = utils.clean_channel_name(channel)
            challenger = utils.clean_channel_name(challenger)
            opponent = utils.clean_channel_name(opponent)
            if winner:
                winner = utils.clean_channel_name(winner)

            channel_discord_user_id = self._get_discord_id(channel)
            challenger_discord_user_id = self._get_discord_id(challenger)
            opponent_discord_user_id = self._get_discord_id(opponent)
            winner_discord_user_id = None
            if winner and winner != '':
                winner_discord_user_id = self._get_discord_id(winner)
            else:
                winner_discord_user_id = None
                winner = None

            payload = {
                "guild_id": self.settings.discord_guild_id,
                "channel_user_id": str(channel_discord_user_id),
                "channel": channel,
                "challenger_user_id": str(challenger_discord_user_id),
                "challenger": challenger,
                "opponent": opponent,
                "opponent_user_id": str(opponent_discord_user_id),
                "count": count,
                "type": str(type),
                "timestamp": timestamp,
                "winner": winner if winner else None,
                "winner_user_id": str(winner_discord_user_id) if winner_discord_user_id else None,
            }

            if count is None:
                del payload['count']
            if (
                winner is None
                or winner == ''
                or winner == 'None'
                or winner_discord_user_id is None
                or winner_discord_user_id == ''
                or winner_discord_user_id == 'None'
            ):
                # payload['winner'] = None
                # payload['winner_user_id'] = None
                del payload['winner']
                del payload['winner_user_id']
            else:
                payload['winner'] = winner
                payload['winner_user_id'] = str(winner_discord_user_id)

            if challenger is None:
                del payload['challenger']
                del payload['challenger_user_id']

            if opponent is None:
                del payload['opponent']
                del payload['opponent_user_id']

            # timestamp within 2 minutes
            timestamp_2_minutes_ago = timestamp - (2 * 60)
            self.connection.twitch_stream_avatar_duel.update_one(
                {
                    "guild_id": self.settings.discord_guild_id,
                    "$or": [
                        {
                            "channel_user_id": str(channel_discord_user_id),
                            "opponent_user_id": str(opponent_discord_user_id),
                        },
                        {
                            "channel_user_id": str(channel_discord_user_id),
                            "challenger_user_id": str(challenger_discord_user_id),
                        }
                    ],
                    # where type != COMPLETE and type != DECLINED
                    "$and": [
                        {"type": {"$ne": str(StreamAvatarTypes.COMPLETE)}},
                        {"type": {"$ne": str(StreamAvatarTypes.DECLINED)}},
                    ],
                    "timestamp": {"$gte": timestamp_2_minutes_ago},
                },
                {"$set": payload},
                upsert=True,
            )
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def get_twitch_stream_avatar_duel_from_challenger_opponent(
        self, channel: str, challenger: str, opponent: str, type: StreamAvatarTypes = StreamAvatarTypes.ACCEPTED
    ) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()

            # find the open duel from the channel, (challenger or opponent) where the type is START and the timestamp is within the last 5 minutes
            date = datetime.datetime.utcnow()
            timestamp = utils.to_timestamp(date)

            channel = utils.clean_channel_name(channel)
            challenger = utils.clean_channel_name(challenger)
            opponent = utils.clean_channel_name(opponent)

            channel_discord_user_id = self._get_discord_id(channel)
            challenger_discord_user_id = self._get_discord_id(challenger)
            opponent_discord_user_id = self._get_discord_id(opponent)

            return self.connection.twitch_stream_avatar_duel.find_one(
                {
                    "guild_id": self.settings.discord_guild_id,
                    "channel_user_id": str(channel_discord_user_id),
                    "challenger_user_id": str(challenger_discord_user_id),
                    "opponent_user_id": str(opponent_discord_user_id),
                    "type": str(type),
                    # "timestamp": {"$lte": timestamp_2_minutes_ago}
                }
            )
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
            return None

    def close_twitch_stream_avatar_open_duels(self, channel: str) -> None:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()

            # find the open duel from the channel, (challenger or opponent) where the type is START and the timestamp is within the last 5 minutes
            date = datetime.datetime.utcnow()
            timestamp = utils.to_timestamp(date)
            # 5 minutes ago
            timestamp_5_minutes_ago = timestamp - (5 * 60)

            channel = utils.clean_channel_name(channel)

            channel_discord_user_id = self._get_discord_id(channel)
            # close requested or accepted duels that have been open for more than 5 minutes.
            # set them as unknown as the actual state is unknown since they did not close correctly.
            self.connection.twitch_stream_avatar_duel.update_many(
                {
                    "guild_id": self.settings.discord_guild_id,
                    "channel_user_id": str(channel_discord_user_id),
                    "type": {"$eq": str(StreamAvatarTypes.REQUESTED), "$ne": str(StreamAvatarTypes.ACCEPTED)},
                    "timestamp": {"$lte": timestamp_5_minutes_ago},
                },
                {"$set": {"type": str(StreamAvatarTypes.UNKNOWN)}},
            )
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )

    def get_twitch_stream_avatar_duel_from_user(
        self, channel: str, user: str, type: StreamAvatarTypes = StreamAvatarTypes.ACCEPTED
    ) -> typing.Optional[dict]:
        _method = inspect.stack()[0][3]
        try:
            if self.connection is None:
                self.open()

            # find the open duel from the channel, (challenger or opponent) where the type is START and the timestamp is within the last 5 minutes
            date = datetime.datetime.utcnow()
            timestamp = utils.to_timestamp(date)
            # 5 minutes ago
            timestamp_2_minutes_ago = timestamp - (2 * 60)

            channel = utils.clean_channel_name(channel)
            user = utils.clean_channel_name(user)

            channel_discord_user_id = self._get_discord_id(channel)
            user_discord_user_id = self._get_discord_id(user)

            return self.connection.twitch_stream_avatar_duel.find_one(
                {
                    "guild_id": self.settings.discord_guild_id,
                    "channel": channel,
                    "$or": [
                        {
                            "channel_user_id": str(channel_discord_user_id),
                            "opponent_user_id": str(user_discord_user_id),
                            "type": str(type),
                            "timestamp": {"$gte": timestamp_2_minutes_ago},
                            "winner_user_id": None,
                        },
                        {
                            "channel_user_id": str(channel_discord_user_id),
                            "challenger_user_id": str(user_discord_user_id),
                            "type": str(type),
                            "timestamp": {"$gte": timestamp_2_minutes_ago},
                            "winner_user_id": None,
                        },
                    ],
                }
            )
        except Exception as ex:
            self.log(
                level=loglevel.LogLevel.ERROR,
                method=f"{self._module}.{self._class}.{_method}",
                message=f"{ex}",
                stackTrace=traceback.format_exc(),
                channel=None,
            )
