"""
STW Daily Discord bot Copyright 2023 by the STW Daily team.
Please do not skid our hard work.
https://github.com/dippyshere/stw-daily

This file is a custom system for i18n (internationalisation) for STW Daily using a single JSON file
"""
from typing import List
import logging

import discord.client
import discord.ext.commands
import orjson
import babel
from ext.profile.bongodb import get_user_document

logger = logging.getLogger(__name__)


def get_plural_form(count: int) -> str:
    """
    Gets the plural form of a language

    Args:
        count (int): The count to use to determine the plural form

    Returns:
        str: The plural form of the language
    """

    if count == 1:
        return "one"
    return "many"


class I18n:
    """
    I18n class for internationalisation

    Args:
        discord.ext.commands.Bot: The bot
        discord.client.Client: The client
        discord.ext.commands.Context: The context

    Attributes:
        bot (discord.ext.commands.Bot): The bot
        client (discord.client.Client): The client
        context (discord.ext.commands.Context): The context
        i18n_json (dict): The i18n json file

    Methods:
        __init__(self): The constructor
        get(self, key: str, lang: str, *args) -> str: Gets a string from the i18n json file
        get_langs(self) -> List[str]: Gets a list of the available languages
        get_lang(self, user_id: int) -> str: Gets the language of a user
    Examples:
        >>> i18n.get("test", "en", "Hello", "World")
        "Hello World"
    """

    def __init__(self) -> None:
        # load the i18n json file
        with open(f"lang/i18n.json", "rb") as f:
            self.i18n_json = orjson.loads(f.read())

    def get(self, key: str, lang: str, *args) -> str:  # hiiiiiiiiiiiiiiiii
        """
        Gets a string from the i18n json file

        Args:
            key (str): The key of the string in the i18n json file
            lang (str): The language to get the string in
            *args: The arguments to format the string with

        Returns:
            str: The string in the specified language

        Raises:
            KeyError: If the key is not found in the i18n json file

        Examples:
            >>> i18n.get("test", "en", "Hello", "World")
            "Hello World"
        """

        # args = [f"{arg:,}" if isinstance(arg, int) else arg for arg in args]

        try:
            # get the string from the i18n json file
            string = self.i18n_json[lang][key]
            # if "slash" in key or "meta" in key:
            #     string = self.i18n_json[lang][key]
            # else:
            #     return key
        except KeyError:
            # if string not found, first try to get the string in english
            try:
                logger.warning(f"Key {key} not found in language {lang}, trying en")
                string = self.i18n_json["en"][key]
            except KeyError:
                # if string not found in english, return the key
                logger.warning(f"Key {key} not found in language {lang} or en")
                return key

        try:
            # format the string with arguments
            logger.debug(f"Returning {string.format(*args)} for key {key} in language {lang} (args: {args})")
            return string.format(*args)
        except IndexError:
            # if the string has no arguments but arguments were given, just return the string
            logger.debug(f"Returning {string} for key {key} in language {lang} (key: {key}")
            return string

    def get_langs(self) -> List[str]:
        """
        Gets a list of the available languages

        Returns:
            list: A list of the available languages
        """
        # get the list of available languages
        logger.debug(f"Returning {list(self.i18n_json.keys())} for get_langs")
        return list(self.i18n_json.keys())

    def get_langs_str(self) -> str:
        """
        Gets a string of the available languages

        Returns:
            str: A string of the available languages
        """
        # get the string of available languages
        logger.debug(f"Returning {', '.join(self.get_langs())} for get_langs_str")
        return ", ".join(self.get_langs())

    def is_lang(self, lang: str) -> bool:
        """
        Checks if a language is valid

        Args:
            lang (str): The language to check

        Returns:
            bool: True if the language is valid, False if the language is not valid
        """
        # check if the language is valid
        logger.debug(f"Returning {lang in self.get_langs()} for is_lang({lang})")
        return lang in self.get_langs()

    def resolve_plural(self, lang: str, key: str, count: int) -> str:
        """
        Resolves a plural string from the i18n json file

        Args:
            lang (str): The language to get the string in
            key (str): The key of the string in the i18n json file
            count (int): The count to use to determine the plural form

        Returns:
            str: The plural string in the specified language
        """
        # get the plural string from the i18n json file
        plural_string = self.i18n_json[lang]["plural"][key]

        # get the plural form
        plural_form = get_plural_form(count)

        # get the plural string from the plural form
        plural_string = plural_string[plural_form]

        try:
            # format the string with the count
            logger.debug(f"Returning {plural_string.format(count)} for key {key} in language {lang} (key: {key}, count: {count})")
            return plural_string.format(count)
        except IndexError:
            # if the string has no arguments, return the string
            logger.debug(f"Returning {plural_string} for key {key} in language {lang} (key: {key}")
            return plural_string

    async def get_desired_lang(self, client: discord.Client, ctx: discord.ext.commands.Context) -> str:
        """
        Calculates the language to use based on the user's preferred language and the server's preferred language

        Args:
            client (discord.Client): The discord client
            ctx (discord.ext.commands.Context): The context to get the language from

        Returns:
            str: The desired language
        """
        # get the user's preferred language
        try:
            user_profile = await get_user_document(ctx, client, ctx.author.id)
            profile_language = user_profile["profiles"][str(user_profile["global"]["selected_profile"])]["settings"][
                "language"]
            if profile_language == "auto" or not self.is_lang(profile_language):
                profile_language = None
        except:
            profile_language = None
        try:
            interaction_language = ctx.interaction.locale
            if interaction_language.lower() in ["en-us", "en-gb", "en"]:
                interaction_language = "en"
            elif interaction_language.lower() in ["zh-cn", "zh-sg", "zh-chs", "zh-hans", "zh-hans-cn", "zh-hans-sg"]:
                interaction_language = "zh-CHS"
            elif interaction_language.lower() in ["zh-tw", "zh-hk", "zh-mo", "zh-cht", "zh-hant", "zh-hant-tw",
                                                  "zh-hant-hk", "zh-hant-mo"]:
                interaction_language = "zh-CHT"
            if not self.is_lang(interaction_language):
                interaction_language = None
        except:
            interaction_language = None
        try:
            guild_language = ctx.guild.preferred_locale
            if guild_language.lower() in ["en-us", "en-gb", "en"]:
                guild_language = "en"
            elif guild_language.lower() in ["zh-cn", "zh-sg", "zh-chs", "zh-hans", "zh-hans-cn", "zh-hans-sg"]:
                guild_language = "zh-CHS"
            elif guild_language.lower() in ["zh-tw", "zh-hk", "zh-mo", "zh-cht", "zh-hant", "zh-hant-tw",
                                            "zh-hant-hk", "zh-hant-mo"]:
                guild_language = "zh-CHT"
            if not self.is_lang(guild_language):
                guild_language = None
        except:
            guild_language = None

        # return the desired language
        logger.debug(f"Returning {profile_language or interaction_language or guild_language or 'en'} for get_desired_lang")
        return profile_language or interaction_language or guild_language or "en"

    def construct_slash_dict(self, key: str) -> dict:
        """
        Constructs a dict of all the localised strings for a slash commands property

        Args:
            key (str): The key to build a dict for

        Returns:
            dict: The localised dict
        """
        # construct the slash dict
        slash_dict = {}
        for lang in self.get_langs():
            if lang == "en":
                slash_dict["en-US"] = self.get(key, lang)
                slash_dict["en-GB"] = self.get(key, lang)
            elif lang == "zh-CHS":
                slash_dict["zh-CN"] = self.get(key, lang)
            elif lang == "zh-CHT":
                slash_dict["zh-TW"] = self.get(key, lang)
            else:
                slash_dict[lang] = self.get(key, lang)
        return slash_dict
