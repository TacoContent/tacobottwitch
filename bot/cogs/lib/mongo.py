from pymongo import MongoClient
import traceback
import json
import typing
import datetime
import pytz
import uuid
from . import utils
from . import settings
from . import loglevel


class MongoDatabase:
    def __init__(self):
        self.client = None
        self.connection = None
        self.settings = settings.Settings()
        pass

    def open(self):
        if not self.settings.db_url:
            raise ValueError("MONGODB_URL is not set")
        self.client = MongoClient(self.settings.db_url)
        self.connection = self.client.tacobot

    def close(self):
        try:
            if self.client:
                self.client.close()
        except Exception as ex:
            print(ex)
            traceback.print_exc()

    def insert_log(self, channel: str, level: loglevel.LogLevel, method: str, message: str, stackTrace: str = None):
        try:
            if self.connection is None:
                self.open()
            payload = {
                "channel: ": channel.strip().lower(),
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

    def clear_log(self, channel: str):
        try:
            if self.connection is None:
                self.open()
            self.connection.logs.delete_many({"channel": channel.strip().lower()})
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        finally:
            self.close()

    def get_bot_twitch_channels(self):
        try:
            if self.connection is None:
                self.open()
            result = self.connection.twitch_channels.find({"guild_id": self.settings.discord_guild_id})
            if result:
                return [f"#{x['channel'].lower().strip()}" for x in result] + self.settings.default_channels
            else:
                print(f"Unable to find channels for bot")
                return self.settings.default_channels
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_any_invite(self):
        try:
            if self.connection is None:
                self.open()
            result = self.connection.invite_codes.find_one({"guild_id": self.settings.discord_guild_id})
            if result:
                return result
            else:
                print(f"Unable to find invite code for bot")
                return None
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_invite_for_user(self, twitch_name: str):
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

    def get_discord_id_for_twitch_username(self, username: str):
        try:
            return self._get_discord_id(username)
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            return None
        finally:
            self.close()

    def get_tqotd(self):
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

    def _get_discord_id(self, username: str):
        if self.connection is None:
            self.open()
        result = self.connection.twitch_user.find_one({"twitch_name": username})
        if result:
            return result["user_id"]
        else:
            return None

    def set_twitch_discord_link_code(self, username: str, code: str):
        try:
            if self.connection is None:
                self.open()
            discord_user_id = self._get_discord_id(username)
            if not discord_user_id:
                payload = {"twitch_name": username.strip().lower(), "link_code": code.strip()}
                self.connection.twitch_user.update_one(
                    {"twitch_name": username.strip().lower()}, {"$set": payload}, upsert=True
                )
                return True
            else:
                raise ValueError(f"Twitch user {username} already linked")
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            raise ex
        finally:
            self.close()

    def link_twitch_to_discord_from_code(self, twitch_name: str, code: str):
        try:
            if self.connection is None:
                self.open()
            discord_user_id = self._get_discord_id(twitch_name)
            if not discord_user_id:
                result = self.connection.twitch_user.find_one({"link_code": code.strip()})
                if result:
                    payload = {
                        "twitch_name": twitch_name.strip().lower(),
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
