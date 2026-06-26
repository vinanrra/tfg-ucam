# Unify API search and process data at another fuction
import json
import logging

import aiohttp
from async_lru import alru_cache


@alru_cache(ttl=120)
async def albionApi(type: str, search_query: str, region: str) -> dict:
    """
    Queries the Albion Online API for information on:
        players
        guilds
        guild members
        alliances
        searches

    Args:
        type (str): The type of query to make.
            Can be "player", "guild", "guild_members", "alliance", or "search".
        search_query (str): The search term to use for the query.

    Raises:
        Exception: If the `type` argument is not one of the valid options.

    Returns:
        dict: A dictionary containing the result of the API query,
            including whether the query was successful and any data returned by the API.
    """

    if region == "East":
        regionUrl = "gameinfo-sgp"
    elif region == "West":
        regionUrl = "gameinfo"
    elif region == "Europe":
        regionUrl = "gameinfo-ams"
    else:
        raise Exception("Region not found")

    if type == "player":
        api_url = (
            f"https://{regionUrl}.albiononline.com/api/gameinfo/players/{search_query}"
        )
    elif type == "guild":
        api_url = (
            f"https://{regionUrl}.albiononline.com/api/gameinfo/guilds/{search_query}/"
        )
    elif type == "guild_members":
        api_url = f"https://{regionUrl}.albiononline.com/api/gameinfo/guilds/{search_query}/members"
    elif type == "alliance":
        api_url = f"https://{regionUrl}.albiononline.com/api/gameinfo/alliances/{search_query}/"
    elif type == "search":
        api_url = (
            f"https://{regionUrl}.albiononline.com/api/gameinfo/search?q={search_query}"
        )
    else:
        raise Exception("Search type not found")

    logging.info(api_url)

    async with aiohttp.ClientSession() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0"
        }
        try:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 404:
                    api_result = {"Found": False}
                # Load response as dict
                elif response.status == 200:
                    data_dict = json.dumps(await response.json())
                    # Load dict to json
                    api_result = json.loads(data_dict)
                    # Because guild_members return a list
                    if type != "guild_members":
                        api_result["Found"] = True
                    if (
                        type == "search"
                        and len(api_result["players"]) == 0
                        and len(api_result["guilds"]) == 0
                    ):
                        api_result = {"Found": False}
                else:
                    api_result = {"Found": "Error"}
        except aiohttp.ClientConnectorError as e:
            # If empty guildID shows error
            api_result = {"Found": "Error"}
            logging.info(f"albionApi - ERROR - Search query: {search_query} - {e}")
        except json.decoder.JSONDecodeError as e:
            api_result = {"Found": False}
            logging.info(f"albionApi - ERROR - Search query: {search_query} - {e}")

    logging.info(f"albionApi - Search query: {search_query}")
    logging.debug(f"Search result: {api_result}")
    return api_result
