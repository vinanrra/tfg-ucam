import re
from datetime import datetime

import nextcord


async def check_api_result(result_api):
    """Checks the result of an API query and returns an error message if the query failed or did not return any data.

    Args:
        result_api: The result of the API query.

    Returns:
        A `nextcord.Embed` object containing an error message if the query failed or did not return any data, otherwise
        `False`.
    """

    embed_api_error = False

    if result_api == "Error":
        embed_api_error = nextcord.Embed(
            title="Albion API Error",
            description="Try again, if the problem persist contact with [Support Server](https://discord.gg/wxaqGTZWXS) for more info.",
        )

    elif result_api is False:
        embed_api_error = nextcord.Embed(
            title="Not found",
            description="This search got no results, if you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS) for more info.",
        )

    return embed_api_error


async def check_articles(string: str):
    """
    A function that removes the articles "the", "The", "el", "la", "El", "La", "los", "las", "Los", "Las" from the beginning of the given string.
    This is useful when working with sorting or searching for names of things, as articles do not add any meaning to the name of the thing.

    Parameters:
        string (str) : The string from which the articles will be removed.

    Returns:
        str : The string with the articles removed from the beginning
    """
    string_no_articles = re.sub(r"^(the|The|el|la|El|La|los|las|Los|Las)\s", "", string)
    return string_no_articles


async def format_discord_user_ids(discordUserIds: str):
    """
    Formats a string of Discord user IDs by adding a space between mentions and removing non-mentions.

    Parameters:
        discordUserIds (str): A string of Discord user IDs.

    Returns:
        List[str]: A list of formatted Discord user IDs.
    """
    # Replace the string "><@" with "> <@" to add a space between mentions
    discordUserIdsFormatted = discordUserIds.replace("><@", "> <@")
    # Split the string on spaces and keep only items that start with "<@"
    listDiscordUserIds = [
        item for item in discordUserIdsFormatted.split(" ") if item.startswith("<@")
    ]

    return listDiscordUserIds


async def enumerate_list(listDiscordUserIds: list):
    """
    This function takes a list of Discord user IDs as an input and returns a formatted string.
    The formatting includes enumerating the items in the list and adding a number and period before each item.

    Parameters:
        listDiscordUserIds (list): A list of Discord user IDs

    Returns:
        str: A formatted string of the Discord user IDs with enumeration and period.
    """
    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(listDiscordUserIds))


async def check_valid_chars(interaction: nextcord.Interaction, discordUserIds: str):
    """
    A function that checks if the given discordUserIds contains only valid characters.
    The valid characters are: <, >, @, 0-9, and space.

    Parameters:
        interaction (nextcord.Interaction) : The interaction object that contains the response object to send the message.
        discordUserIds (str) : The string to check for valid characters.

    Returns:
        None : If the string contains invalid characters, an error message will be sent using the interaction object and the function will return
    """
    valid_chars = set(" <>@0123456789")
    if not set(discordUserIds).issubset(valid_chars):
        embed_invalid_char = nextcord.Embed(title="ERROR")
        embed_invalid_char.add_field(
            name="The string contains invalid characters",
            value="The list can only contains @MENTIONS, verify that you list doesn't contain anything else",
            inline=False,
        )
        await interaction.response.send_message(
            embed=embed_invalid_char,
        )
        return


async def check_valid_date(interaction: nextcord.Interaction, date: str):
    """
    A function that checks if the given date is a valid date in the given format.
    The default date format is "%d/%m/%Y" (day/month/year).

    Parameters:
        interaction (nextcord.Interaction) : The interaction object that contains the response object to send the message.
        date (str) : The string to check if it's a valid date.

    Returns:
        None : If the string is not a valid date, an error message will be sent using the interaction object and the function will return
    """
    date_format = "%d/%m/%Y"
    try:
        datetime.strptime(date, date_format)
    except ValueError:
        embed_invalid_date = nextcord.Embed(title="ERROR")
        embed_invalid_date.add_field(
            name="The string is not a valid date in the format {}".format(date_format),
            inline=False,
        )
        await interaction.response.send_message(embed=embed_invalid_date)
        return


async def check_string_length(
    interaction: nextcord.Interaction, string: str, string_name: str, max_lenght: int
):
    """
    A function that checks if the given string is less than or equal to max_lenght characters.

    Parameters:
        interaction (nextcord.Interaction) : The interaction object that contains the response object to send the message.
        string (str) : The loot name to check its length.

    Returns:
        None : If the string is greater than max_lenght characters, an error message will be sent using the interaction object and the function will return
    """
    if len(string) > max_lenght:
        embed_tooLong = nextcord.Embed(
            title="Error:",
            description=f"The maximum characters for {string_name} are {max_lenght}",
        )
        await interaction.response.send_message(embed=embed_tooLong)
        return


async def clean_discord_user_id(discord_user_id: str):
    """
    A function that removes the characters ">, <, @, and," from a given discord user id.

    Parameters:
        discord_user_id (str) : The discord user id to clean.

    Returns:
        str : The cleaned discord user id.
    """
    return (
        discord_user_id.replace(">", "")
        .replace(",", "")
        .replace("<", "")
        .replace("@", "")
    )


async def check_valid_id(id: str):
    """
    A function that checks if the given id have ¿?!¡.

    Parameters:
        interaction (nextcord.Interaction) : The interaction object that contains the response object to send the message.
        string (str) : The id.

    Returns:
        None : If the id have invalid characters will show a message.
    """
    pattern = re.compile(r"[¿?!¡]")

    embed_invalid_id = nextcord.Embed(
        title="Error:",
        description="The ID have invalid characters.",
    )

    if bool(pattern.search(id)):
        return True, embed_invalid_id

    return False, embed_invalid_id
