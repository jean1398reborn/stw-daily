"""
STW Daily Discord bot Copyright 2022 by the STW Daily team.
Please do not skid our hard work.
https://github.com/dippyshere/stw-daily
"""
import orjson

print("Starting STW Daily")

import os
import aiohttp
import discord
import discord.ext.commands as ext
from discord.ext import tasks

import stwutil as stw

# Compatability layer for future versions of python 3.11+ 
try:
    import tomllib as toml
except ModuleNotFoundError:
    import tomli as toml

client = ext.AutoShardedBot(command_prefix=ext.when_mentioned, case_insensitive=True)


def load_config(config_path):
    """
    Loads the config file

    Args:
        config_path: The path to the config file

    Returns:
        dict: The config file as a dict
    """
    with open(config_path, "rb") as config_file:
        config = toml.load(config_file)
        config_file.close()

    return config


def main():
    """
    Main function
    """
    # Loading config file
    config_path = "config.toml"
    client.config = load_config(config_path)

    # simple way to parse the colours from config into usable colours;
    client.colours = {}
    for name, colour in client.config["colours"].items():
        client.colours[name] = discord.Colour.from_rgb(colour[0], colour[1], colour[2])

    client.temp_auth = {}
    client.remove_command('help')

    # list of extensions for stw daily to load in
    extensions = [
        "reward",
        "help",
        "auth",
        "daily",
        "info",
        "research",
        "serverext",
        "homebase",
        "vbucks",
        "reload",
        "profile.lavendar",
        "profile.devauth",
        "profile.sunday",
        "news",
        "battlebreakers.battlebreakers",  # why do you only call me when you're high
        "battlebreakers.bbreward",
        "power",
        "i18n-testing",
        "invite",
    ]  # why no ext.bongodb :( doot doot doot doot
    # load the extensions
    client.a = "✅ Official Verified Deployment", True  # seleckted
    for ext in extensions:
        print(client.load_extension(f"ext.{ext}"))

    update_status.start()
    client.run(f"{os.environ['STW_DAILY_TOKEN']}")


async def create_http_session():
    """
    Creates an aiohttp session

    Returns:
        aiohttp.ClientSession: The aiohttp session
    """
    return aiohttp.ClientSession(json_serialize=lambda x: orjson.dumps(x).decode())


# basic information for you <33
@client.event
async def on_ready():
    """
    Event for when the bot is ready
    """
    client.stw_session = await create_http_session()
    for command in client.commands:
        if command.name == "auth":
            client.auth_command = command
            break

    client.localisation = stw.reverse_dict_with_list_keys(client.config["valid_locales"])
    client.command_name_dict, client.command_dict, client.command_name_list = stw.create_command_dict(client)
    print("Started STW Daily")


@client.event
async def on_message(message):
    """
    Event for when a message is sent.
    This works without message.content, and is currently used to: handle quote marks, auth by default

    Args:
        message: The message that was sent

    Returns:
        None
    """
    if '"' in message.content:
        message = stw.process_quotes_in_message(message)

    # pro watch me i am the real github copilot
    # make epic auth system thing
    try:
        if len(stw.extract_auth_code(message.content.split(" ")[1])) == 32:
            await client.auth_command.__call__(message, stw.extract_auth_code(message.content))
            return
    except IndexError:
        pass

    await client.process_commands(message)


# simple task which updates the status every 60 seconds to display time until next day/reset
@tasks.loop(seconds=60)
async def update_status():
    """
    Task to update the status of the bot
    """
    await client.wait_until_ready()
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening,
                                  name=f"@{client.user.name}  |  Reset in: \n{stw.time_until_end_of_day()}\n  |  In {len(client.guilds)} guilds"))


if __name__ == "__main__":
    main()
