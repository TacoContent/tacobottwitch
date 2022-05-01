from operator import truediv
from pymongo import MongoClient
import traceback
import json
import typing
import datetime
import random
import pytz
import uuid
from . import utils
from . import settings
from . import loglevel


class MongoDatabase:
    def __init__(self) -> None:
        self.client = None
        self.connection = None
        self.settings = settings.Settings()
        pass

    def open(self) -> None:
        if not self.settings.db_url:
            raise ValueError("MONGODB_URL is not set")
        self.client = MongoClient(self.settings.db_url)
        self.connection = self.client.tacobot

    def close(self) -> None:
        try:
            if self.client:
                self.client.close()
        except Exception as ex:
            print(ex)
            traceback.print_exc()

    def insert_log(self, channel: str, level: loglevel.LogLevel, method: str, message: str, stackTrace: str = None) -> None:
        try:
            if self.connection is None:
                self.open()
            payload = {
                "channel: ": utils.clean_channel_name(channel),
                "timestamp": utils.get_timestamp(),
                "level": level.name,
                "method": method,
                "message": message,
                "stack_trace": stackTrace,
            }
            self.connection.logs.insert_one(payload)
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        finally:
            self.close()

    def clear_log(self, channel: str) -> None:
        try:
            if self.connection is None:
                self.open()
            channel = utils.clean_channel_name(channel)
            self.connection.logs.delete_many({"channel": channel})
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        finally:
            self.close()

    def get_channel_settings(self, channel: str) -> dict:
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
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()
            pass

    def set_channel_settings(self, channel: str, settings: dict) -> None:
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
            print(ex)
            traceback.print_exc()
            raise ex
        finally:
            self.close()
            pass

    def get_settings(self, name: str) -> dict:
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
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def get_bot_twitch_channels(self) -> typing.List[str]:
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
                print(f"Unable to find channels for bot")
                return self.settings.default_channels
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def add_bot_to_channel(self, twitch_channel) -> None:
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
            raise ve
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            raise ex
        finally:
            self.close()

    def remove_bot_from_channel(self, twitch_channel) -> bool:
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
            raise ve
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            raise ex
        finally:
            self.close()

    def get_any_invite(self) -> dict:
        try:
            if self.connection is None:
                self.open()
            # get the count of all invites
            invite_count = self.connection.invite_codes.count()
            # get a random number between 0 and the count of invites
            rand_index = random.randint(0, invite_count)
            # get the invite at the random index and take 1 item
            result = self.connection.invite_codes.find({"guild_id": self.settings.discord_guild_id}).skip(rand_index)

            if result:
                return result[0]
            else:
                print(f"Unable to find invite code for bot")
                return None
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_invite_for_user(self, twitch_name: str) -> dict:
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
                    print(f"Unable to find invite code for twitch user {twitch_name}")
                    return None
            else:
                return None
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_discord_id_for_twitch_username(self, username: str) -> str:
        try:
            return self._get_discord_id(username)
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_tqotd(self) -> str:
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
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def _get_discord_id(self, username: str) -> str:
        if self.connection is None:
            self.open()
        username = utils.clean_channel_name(username)
        result = self.connection.twitch_user.find_one({"twitch_name": username})
        if result:
            return result["user_id"]
        else:
            return None

    def update_twitch_user(self, name: str, user_id: str) -> None:
        pass

    def set_twitch_discord_link_code(self, username: str, code: str) -> bool:
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
            print(ex)
            traceback.print_exc()
            raise ex
        finally:
            self.close()

    def link_twitch_to_discord_from_code(self, twitch_name: str, code: str) -> bool:
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
            print(ex)
            traceback.print_exc()
            raise ex
        finally:
            self.close()

    def get_top_tacos_leaderboard(self, limit: int = 10) -> list:
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
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_tacos_count(self, twitch_name: str) -> int:
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
                print(
                    f"[DEBUG] [mongo.get_tacos_count] [channel:none] User {twitch_name}[{discord_user_id}] not in table"
                )
                return 0
            return data["count"]
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def add_tacos(self, twitch_name: str, count: int) -> int:
        try:
            if self.connection is None:
                self.open()
            twitch_name = utils.clean_channel_name(twitch_name)
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                return 0

            user_tacos = self.get_tacos_count(twitch_name=twitch_name)
            if user_tacos is None:
                print(f"[DEBUG] [mongo.add_tacos] [channel:none] User {twitch_name}[{discord_user_id}] not in table")
                user_tacos = 0
            else:
                user_tacos = user_tacos or 0
                print(
                    f"[DEBUG] [mongo.add_tacos] [channel:none] User {twitch_name}[{discord_user_id}] has {user_tacos} tacos"
                )

            user_tacos += count
            print(
                f"[DEBUG] [mongo.add_tacos] [channel:none] User {twitch_name}[{discord_user_id}] now has {user_tacos} tacos"
            )
            self.connection.tacos.update_one(
                {"guild_id": self.settings.discord_guild_id, "user_id": discord_user_id},
                {"$set": {"count": user_tacos}},
                upsert=True,
            )
            return user_tacos
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def remove_tacos(self, twitch_name: str, count: int) -> int:
        try:
            if count < 0:
                print(f"[DEBUG] [mongo.remove_tacos] [channel:none] Count is less than 0")
                return 0
            if self.connection is None:
                self.open()
            twitch_name = utils.clean_channel_name(twitch_name)
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                return 0

            user_tacos = self.get_tacos_count(twitch_name=twitch_name)
            if user_tacos is None:
                print(f"[DEBUG] [mongo.remove_tacos] [channel:none] User {twitch_name}[{discord_user_id}] not in table")
                user_tacos = 0
            else:
                user_tacos = user_tacos or 0
                print(
                    f"[DEBUG] [mongo.remove_tacos] [channel:none] User {twitch_name}[{discord_user_id}] has {user_tacos} tacos"
                )

            user_tacos -= count
            if user_tacos < 0:
                user_tacos = 0

            print(
                f"[DEBUG] [mongo.remove_tacos] [channel:none] User {twitch_name}[{discord_user_id}] now has {user_tacos} tacos"
            )
            self.connection.tacos.update_one(
                {"guild_id": self.settings.discord_guild_id, "user_id": discord_user_id},
                {"$set": {"count": user_tacos}},
                upsert=True,
            )
            return user_tacos
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def track_taco_gift(self, channel: str, user: str, amount: int, reason: str = None) -> None:
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
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def get_total_gifted_tacos(self, channel: str, timespan_seconds: int = 86400) -> int:
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
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def get_total_gifted_tacos_to_user(self, channel: str, user: str, timespan_seconds: int = 86400) -> int:
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
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()

    def track_user_message_in_chat(self, channel: str, user: str, message: str, timespan_seconds: int = 86400) -> bool:
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
                        {
                            "guild_id": self.settings.discord_guild_id,
                            "channel": channel,
                            "twitch_name": user,
                        },
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
            print(ex)
            traceback.print_exc()
        finally:
            if self.connection:
                self.close()
