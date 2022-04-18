import sys
import os
import traceback
import glob
import typing
from . import utils
import json
from . import logger
from . import loglevel
import inspect

class Settings:
    APP_VERSION = "1.0.0-snapshot"
    BITRATE_DEFAULT = 64

    def __init__(self):
        try:
            with open('app.manifest', encoding="UTF-8") as json_file:
                self.__dict__.update(json.load(json_file))
        except Exception as e:
            print(e, file=sys.stderr)

        self.twitch_client_id = utils.dict_get(os.environ, 'TWITCH_CLIENT_ID', default_value= None)
        self.twitch_client_secret = utils.dict_get(os.environ, 'TWITCH_CLIENT_SECRET', default_value= None)
        self.twitch_oauth_token = utils.dict_get(os.environ, 'TWITCH_OAUTH_TOKEN', default_value= None)
        self.twitch_team_name = utils.dict_get(os.environ, 'TWITCH_TEAM_NAME', default_value= "taco")
        self.discord_guild_id = utils.dict_get(os.environ, 'DISCORD_GUILD_ID', default_value= "935294040386183228")
        self.bot_prefixes = [ f"{p.lower().lstrip()}" for p in utils.dict_get(os.environ, 'BOT_PREFIXES', default_value="!").split(",")]
        self.bot_owner = utils.dict_get(os.environ, 'BOT_OWNER', default_value= 'darthminos')
        self.bot_name = utils.dict_get(os.environ, 'BOT_NAME', default_value= 'ourtacobot')
        self.default_channels = [f"#{c.strip().lower()}" for c in utils.dict_get(os.environ, 'DEFAULT_CHANNELS', default_value= 'darthminos,ourtaco,ourtacobot').split(',')]
        self.log_level = utils.dict_get(os.environ, 'LOG_LEVEL', default_value = 'DEBUG')
        self.language = utils.dict_get(os.environ, "LANGUAGE", default_value = "en-us").lower()
        self.db_url = utils.dict_get(os.environ, "MONGODB_URL", default_value = "mongodb://localhost:27017/tacobot")
        self.timezone = utils.dict_get(os.environ, "TIMEZONE", default_value = "America/Chicago")
        self.discord_guild_id = utils.dict_get(os.environ, "DISCORD_GUILD_ID", default_value = "")

        # log_level = loglevel.LogLevel[self.log_level.upper()]
        # if not log_level:
        #     log_level = loglevel.LogLevel.DEBUG

        # self.log = logger.Log(minimumLogLevel=self.log_level)

        self.load_language_manifest()
        self.load_strings()

    def get_settings(self, db, guildId: int, name:str):
        return db.get_settings(guildId, name)

    def get_string(self, guildId: int, key: str, *args, **kwargs):
        _method = inspect.stack()[1][3]
        if not key:
            # self.log.debug(guildId, _method, f"KEY WAS EMPTY")
            return ''
        if str(guildId) in self.strings:
            if key in self.strings[str(guildId)]:
                return utils.str_replace(self.strings[str(guildId)][key], *args, **kwargs)
            elif key in self.strings[self.language]:
                # self.log.debug(guildId, _method, f"Unable to find key in defined language. Falling back to {self.language}")
                return utils.str_replace(self.strings[self.language][key], *args, **kwargs)
            else:
                # self.log.warn(guildId, _method, f"UNKNOWN STRING KEY: {key}")
                print(f"UNKNOWN KEY: LANG: {self.language} - {key}", file=sys.stderr)
                return utils.str_replace(f"{key}", *args, **kwargs)
        else:
            if key in self.strings[self.language]:
                return utils.str_replace(self.strings[self.language][key], *args, **kwargs)
            else:
                # self.log.warn(guildId, _method, f"UNKNOWN STRING KEY: {key}")
                print(f"UNKNOWN KEY: LANG: {self.language} - {key}", file=sys.stderr)
                return utils.str_replace(f"{key}", *args, **kwargs)

    def set_guild_strings(self, guildId: int, lang: str = None):
        _method = inspect.stack()[1][3]
        # guild_settings = self.db.get_guild_settings(guildId)
        if not lang:
            lang = self.language
        # if guild_settings:
        #     lang = guild_settings.language
        self.strings[str(guildId)] = self.strings[lang]
        # self.log.debug(guildId, _method, f"Guild Language Set: {lang}")

    def get_language(self, guildId: int):
        # guild_setting = self.db.get_guild_settings(guildId)
        # if not guild_setting:
        return self.language
        # return guild_setting.language or self.settings.language

    def load_strings(self):
        _method = inspect.stack()[1][3]
        self.strings = {}

        lang_files = glob.glob(os.path.join(os.path.dirname(__file__), "../../../languages", "[a-z][a-z]-[a-z][a-z].json"))
        languages = [os.path.basename(f)[:-5] for f in lang_files if os.path.isfile(f)]
        for lang in languages:
            self.strings[lang] = {}
            try:
                lang_json = os.path.join("languages", f"{lang}.json")
                if not os.path.exists(lang_json) or not os.path.isfile(lang_json):
                    # self.log.error(0, "settings.load_strings", f"Language file {lang_json} does not exist")
                    # THIS SHOULD NEVER GET HERE
                    continue

                with open(lang_json, encoding="UTF-8") as lang_file:
                    self.strings[lang].update(json.load(lang_file))
            except Exception as e:
                print(f"{e}", file=sys.stderr)
                traceback.print_exc()
                # self.log.error(0, "settings.load_strings", str(e), traceback.format_exc())


    def load_language_manifest(self):
        lang_manifest = os.path.join(os.path.dirname(__file__), "../../../languages/manifest.json")
        self.languages = {}
        if os.path.exists(lang_manifest):
            with open(lang_manifest, encoding="UTF-8") as manifest_file:
                self.languages.update(json.load(manifest_file))
