import re
from twitchio.ext import commands
import twitchio
import os
import traceback
import sys
import json
import inspect
import asyncio
import math

from .lib import mongo
from .lib import settings
from .lib import utils
from .lib import loglevel
from .lib import logger
from .lib import permissions
from .lib import command_helper
from .lib import tacos_log as tacos_log
from .lib import tacotypes

# PokemonCommunityGameCog: TwitchLit A wild Cacturne appears TwitchLit Catch it using !pokecatch (winners revealed in 90s)


class PokemonCommunityGameCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:

        self.bot = bot
        self.db = mongo.MongoDatabase()
        self.settings = settings.Settings()
        self.tacos_log = tacos_log.TacosLog(self.bot)

        self.start_commands = ["start", "on", "enable"]
        self.stop_commands = ["stop", "off", "disable"]

        self.bot_user = "pokemoncommunitygame"

        self.balance_regex = re.compile(
            r"^\@ourtacobot\'s\sBalance:\s\$(?P<balance>\d{1,})\s🏹",
            re.MULTILINE | re.IGNORECASE,
        )

        self.pokemon_regex = re.compile(
            r"(?:\u0001ACTION\s)?TwitchLit\sA\swild\s(?P<pokemon>(?:\w\s?)+)\sappears\sTwitchLit\sCatch\sit\susing\s!pokecatch",
            re.MULTILINE | re.IGNORECASE,
        )

        self.no_trainer_regex = re.compile(
            r"\@ourtacobot\sYou\sdon\'t\shave\sa\strainer\spass\syet\s🤨\sEnter\s!pokestart",
            re.MULTILINE | re.IGNORECASE,
        )

        self.no_ball_regex = re.compile(
            r"\@ourtacobot\sYou\sdon\'t\sown\sthat\sball\.\sCheck\sthe\sextension\sto\ssee\syour\sitems",
            re.MULTILINE | re.IGNORECASE,
        )

        self.purchase_success_regex = re.compile(r"\@ourtacobot\sPurchase\ssuccessful!", re.MULTILINE | re.IGNORECASE)

        self.not_enough_money_regex = re.compile(
            r"\@ourtacobot\sYou\sdon\'t\shave\senough\sPoké-Dollars.\sYou\sneed:\s\$\d{1,}",
            re.MULTILINE | re.IGNORECASE,
        )

        self.pokecheck_no_regex = re.compile(
            r"\@ourtacobot\s(?P<pokemon>(?:\w\s?)+)\sregistered\sin\sPokédex:\s❌", re.MULTILINE | re.IGNORECASE
        )
        # @ourtacobot Lopunny registered in Pokédex: ✔
        self.pokecheck_yes_regex = re.compile(
            r"\@ourtacobot\s(?P<pokemon>(?:\w\s?)+)\sregistered\sin\sPokédex:\s✔", re.MULTILINE | re.IGNORECASE
        )

        # try and get the suggested ball to use. then check if we have that ball. if not, try to buy it. if not successful, use a regular pokeball

        log_level = loglevel.LogLevel[self.settings.log_level.upper()]
        if not log_level:
            log_level = loglevel.LogLevel.DEBUG

        self.log = logger.Log(minimumLogLevel=log_level)
        self.permissions_helper = permissions.Permissions()
        self.log.debug("NONE", "pokemon.__init__", "Initialized")

    @commands.command(name="pokemon")
    async def pokemon(self, ctx: commands.Context, subcommand: str = None, *args) -> None:
        _method = inspect.stack()[1][3]

        if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.EVERYONE):
            self.log.debug(
                ctx.message.channel.name,
                _method,
                f"{ctx.message.author.name} does not have permission to use this command.",
            )
            return

        if subcommand is not None:
            if subcommand.lower() in self.stop_commands:
                await self._pokemon_stop(ctx, args)
            elif subcommand.lower() in self.start_commands:
                await self._pokemon_start(ctx, args)

    async def _pokemon_stop(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        try:
            channel = utils.clean_channel_name(ctx.channel.name)

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    _method,
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, "pokemon.pokemon_stop", f"Stopping pokemon event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            channel_settings[self.bot_user]["enabled"] = False
            self.settings.set_channel_settings(self.db, channel, channel_settings)

            await ctx.reply(
                f"@{ctx.message.author.name}, I will no longer participate in the pokemon community game. You can start it again with `{prefix}pokemon start`."
            )
        except Exception as e:
            self.log.error(channel, "pokemon.pokemon_stop", str(e), traceback.format_exc())

    async def _pokemon_start(self, ctx: commands.Context, args) -> None:
        _method = inspect.stack()[1][3]
        try:
            channel = utils.clean_channel_name(ctx.message.channel.name)

            if channel is None:
                return

            if not self.permissions_helper.has_permission(ctx.message.author, permissions.PermissionLevel.MODERATOR):
                self.log.debug(
                    channel,
                    _method,
                    f"{ctx.message.author.name} does not have permission to use this command.",
                )
                return

            self.log.debug(channel, "pokemon.pokemon_start", f"Starting pokemon event in {channel}")
            prefixes = self.settings.prefixes
            if not prefixes:
                prefixes = ["!taco "]
            prefix = prefixes[0]

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            channel_settings[self.bot_user]["enabled"] = True
            self.settings.set_channel_settings(self.db, channel, channel_settings)

            await ctx.reply(
                f"@{ctx.message.author.name}, I will now participate in the pokemon community game. You can stop it with `{prefix}pokemon stop`."
            )
        except Exception as e:
            self.log.error(channel, "pokemon.pokemon_start", str(e), traceback.format_exc())

    @commands.Cog.event()
    # https://twitchio.dev/en/latest/reference.html#twitchio.Message
    async def event_message(self, message) -> None:
        try:
            if message.author is None or message.channel is None:
                return

            sender = utils.clean_channel_name(message.author.name)
            channel = utils.clean_channel_name(message.channel.name)
            ctx_channel = self.bot.get_channel(channel)

            channel_settings = self.settings.get_channel_settings(self.db, channel)
            game_settings = channel_settings.get(self.bot_user, {"enabled": True})
            if not game_settings.get("enabled", True):
                return

            if sender == channel or not ctx_channel:
                return

            # is the message from the pokemon bot?
            if sender == utils.clean_channel_name(self.bot_user):
                strip_msg = message.content.replace("\u0001ACTION", "").strip()
                # if message.content matches purchase regex
                match = self.pokemon_regex.match(strip_msg)
                if match:
                    pokemon = match.group("pokemon")
                    self.log.debug(channel, "pokemon.event_message", f"check if we have a {pokemon} in the Pokédex.")
                    await asyncio.sleep(1)
                    await ctx_channel.send(f"!pokecheck")
                    return
                match = self.pokecheck_no_regex.match(strip_msg)
                if match:
                    pokemon = match.group("pokemon")
                    self.log.debug(channel, "pokemon.event_message", f"{pokemon} not in Pokédex, lets catch it.")
                    await asyncio.sleep(1)
                    await ctx_channel.send(f"!pokecatch pokeball")
                    return
                match = self.pokecheck_yes_regex.match(strip_msg)
                if match:
                    pokemon = match.group("pokemon")
                    self.log.debug(channel, "pokemon.event_message", f"{pokemon} in Pokédex")
                    # await ctx_channel.send(f"I already have {pokemon} in my Pokédex, so someone else catch it. 😎")
                    return
                match = self.no_trainer_regex.match(strip_msg)
                if match:
                    self.log.debug(channel, "pokemon.event_message", "No trainer found, initiating pokestart")
                    await ctx_channel.send("!pokestart")
                    await asyncio.sleep(3)
                    await ctx_channel.send("!pokecatch pokeball")
                    return
                match = self.no_ball_regex.match(strip_msg)
                if match:
                    self.log.debug(channel, "pokemon.event_message", "No ball found, initiating check balance")
                    await asyncio.sleep(1)
                    await ctx_channel.send("!pokepass")
                    return
                match = self.balance_regex.match(strip_msg)
                if match:
                    balance = match.group("balance")
                    self.log.debug(channel, "pokemon.event_message", f"Balance: ${balance}")
                    await asyncio.sleep(1)
                    if balance.isdigit():
                        balance = int(balance)
                        purchase_count = math.floor(balance / 300)
                        if purchase_count >= 1:
                            await ctx_channel.send(f"!pokeshop pokeball {purchase_count}")
                        else:
                            self.log.debug(
                                channel,
                                "pokemon.event_message",
                                "Not enough money, (${balance}) i'll have to sit this one out...",
                            )
                    return
                match = self.purchase_success_regex.match(strip_msg)
                if match:
                    self.log.debug(channel, "pokemon.event_message", "Purchase successful, initiating pokecatch")
                    await asyncio.sleep(1)
                    await ctx_channel.send("!pokecatch pokeball")
                    return
                match = self.not_enough_money_regex.match(strip_msg)
                if match:
                    self.log.debug(channel, "pokemon.event_message", "Not enough money")
                    # await ctx_channel.send("I need more money! who is giving me money for pokeballs? 🤔")
                    return

                self.log.debug(channel, "pokemon.event_message", f"unknown message: {strip_msg}")
        except Exception as e:
            self.log.error(channel, "pokemon.event_message", str(e), traceback.format_exc())


def prepare(bot) -> None:
    bot.add_cog(PokemonCommunityGameCog(bot))
