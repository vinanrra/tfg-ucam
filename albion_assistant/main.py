import logging
import os
import traceback

import nextcord
from functions.mysql import (
    region_insert,
    registerDeleteDiscord,
    settingsDelete,
    tables_creation,
)
from nextcord.errors import NotFound
from nextcord.ext import commands, tasks
from nextcord.ext.application_checks.errors import (
    ApplicationCheckFailure,
    ApplicationMissingPermissions,
)

intents = nextcord.Intents(members=True, guilds=True)

bot_token = os.environ["TOKEN"]

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

bot = commands.AutoShardedBot(
    intents=intents,
    chunk_guilds_at_startup=False,
    member_cache_flags=nextcord.MemberCacheFlags.none(),
)


# Ignore DMs
@bot.check
async def globally_block_dms(ctx):
    """
    A coroutine function that checks if the command was sent in a DM channel and blocks it.

    Args:
        ctx (commands.Context): The context of the command.

    Returns:
        bool: True if the command was sent in a guild channel, False if it was sent in a DM channel.
    """
    return ctx.guild is not None


@bot.event
async def on_guild_remove(guild):
    """
    A coroutine function that handles the 'guild_remove' event when the bot is removed from a guild.

    Args:
        guild (discord.Guild): The guild that the bot was removed from.

    Returns:
        None
    """
    await settingsDelete(guild.id)


@bot.event
async def on_application_command_error(interaction: nextcord.Interaction, error):
    """
    A coroutine function that handles errors raised when a user interacts with a slash command.

    Args:
        interaction (nextcord.Interaction): The interaction object that triggered the error.
        error (Exception): The error that was raised.

    Returns:
        None
    """
    if isinstance(error, ApplicationMissingPermissions):
        embed_missing_permission = nextcord.Embed(title="Error", description=f"{error}")
        await interaction.response.send_message(
            embed=embed_missing_permission,
        )
    elif isinstance(error, ApplicationCheckFailure):
        embed_missing_permission = nextcord.Embed(
            title="Error", description="You aren't allowed to use this command."
        )
        await interaction.response.send_message(
            embed=embed_missing_permission,
        )
    elif isinstance(error.original, NotFound):
        logging.info(
            "nextcord.errors.NotFound: 404 Not Found (error code: 10062): Unknown interaction"
        )
    else:
        raise error


@bot.event
async def on_ready():
    logging.info("Bot it's ready")


@bot.event
async def on_raw_member_remove(payload):
    """
    A coroutine function that handles the 'raw_member_remove' event when a member leaves a guild.

    Args:
        payload (discord.RawMemberRemoveEvent): The payload of the 'raw_member_remove' event.

    Returns:
        None
    """
    # <RawMemberRemoveEvent guild_id=INT user=<User id=INT name='STR' discriminator='INT' bot=BOOL>>
    regions: list[str] = ["West", "East", "Europe"]
    for region in regions:
        await registerDeleteDiscord(payload.guild_id, payload.user.id, region)


initial_extension = []
# Load cogs in cogs folder and subdirectories
COGS_FOLDER = "cogs"

for folder in os.listdir(f"./{COGS_FOLDER}"):
    for filename in os.listdir(f"./{COGS_FOLDER}/{folder}/."):
        if filename.endswith(".py"):
            initial_extension.append(f"{COGS_FOLDER}.{folder}.{filename[:-3]}")


@tasks.loop(seconds=1.0, count=1)
async def initial_settings():
    """
    A coroutine function that creates database tables, inserts regions, and loads initial extensions.

    Args:
        None

    Returns:
        None
    """
    # Create database tables
    await tables_creation()
    regions = ["West", "East", "Europe"]
    for region in regions:
        await region_insert(region)
    # Load cogs
    for extension in initial_extension:
        try:
            bot.load_extension(extension)
        except Exception:
            logging.info("Failed to load extension %s.", extension)
            traceback.print_exc()


@initial_settings.after_loop
async def after_slow_count():
    logging.info("Initial settings done")


initial_settings.start()

# Start bot with token
bot.run(bot_token, reconnect=True)
