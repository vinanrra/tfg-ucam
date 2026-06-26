import json
import logging
from millify import millify


async def guild_get_members_id(guildUserApiResult):
    """
    Retrieves the list of member IDs from a guild user API result.

    Args:
        guildUserApiResult (dict): A dictionary containing user data for a guild.

    Returns:
        list: A list of member IDs as strings.

    Raises:
        None.

    Example Usage:
        result = await guild_get_members_id(api_result)
        print(result)
    """

    guildMembers = []
    data_dump = json.dumps(guildUserApiResult)
    # Load dict to json
    data_json = json.loads(data_dump)

    for member in data_json:
        try:
            guildMembers.append(member["Id"])
        except TypeError as e:
            logging.info(e)
            pass

    return guildMembers


async def apiSearchPlayerProcess(apiResponseDict: dict, albionUserNick: str):
    """
    Processes a dictionary of API response data for Albion Online player search.

    Args:
        apiResponseDict (dict): A dictionary of API response data for player search.
        albionUserNick (str): The Albion Online user nickname to search for.

    Returns:
        dict: A dictionary containing processed data for the found player.

    Raises:
        None.

    Example Usage:
        result = await apiSearchPlayerProcess(api_response, 'exampleplayer')
        print(result)
    """

    albionUserInfo = {"Found": False}
    # Si players existe en api_response_dict
    max_deathFame = None
    if len(apiResponseDict["players"]) > 1:
        for player in apiResponseDict["players"]:
            playerNameLower = player.get("Name").lower()
            if playerNameLower == f"{albionUserNick.lower()}" and (
                max_deathFame is None
                or int(player.get("DeathFame") or 0) > max_deathFame
            ):
                # Transform deathFame from String to Int, if "" will be 0
                max_deathFame = int(player.get("DeathFame") or 0)
                albionUserInfo = {
                    "Name": player.get("Name"),
                    "Id": player.get("Id"),
                    "GuildName": player.get("GuildName"),
                    "GuildId": player.get("GuildId"),
                    "AllianceName": player.get("AllianceName"),
                    "AllianceId": player.get("AllianceId"),
                    "KillFame": player.get("KillFame"),
                    "DeathFame": player.get("DeathFame"),
                    "Found": True,
                }
    elif len(apiResponseDict["players"]) == 1:
        albionUserInfo = {
            "Name": apiResponseDict["players"][0].get("Name"),
            "Id": apiResponseDict["players"][0].get("Id"),
            "GuildName": apiResponseDict["players"][0].get("GuildName"),
            "GuildId": apiResponseDict["players"][0].get("GuildId"),
            "AllianceName": apiResponseDict["players"][0].get("AllianceName"),
            "AllianceId": apiResponseDict["players"][0].get("AllianceId"),
            "KillFame": apiResponseDict["players"][0].get("KillFame"),
            "DeathFame": apiResponseDict["players"][0].get("DeathFame"),
            "Found": True,
        }

    return albionUserInfo


async def apiSearchGuildProcess(apiResponseDict: dict, albionGuildName: str):
    """
    Processes a dictionary of API response data for Albion Online guild search.

    Args:
        apiResponseDict (dict): The Albion Online API response, as a dictionary.
        albionGuildName (str): The name of the guild to search for.

    Returns:
        dict: A dictionary containing the ID, name, and alliance ID of the guild, if it is found in the API response. If
        the guild is not found in the response, the dictionary will contain only the "Found" key, which will be set to
        False.
    """

    max_death_fame = None
    albion_guild_info = {"Found": False}
    if len(apiResponseDict["guilds"]) > 1:
        for guild in apiResponseDict["guilds"]:
            if guild.get("Name").lower() == f"{albionGuildName.lower()}" and (
                max_death_fame is None
                or int(guild.get("DeathFame") or 0) > max_death_fame
            ):
                albion_guild_info = {
                    "Id": guild.get("Id"),
                    "Name": guild.get("Name"),
                    "AllianceId": guild.get("AllianceId"),
                    "Found": True,
                }
    elif len(apiResponseDict["guilds"]) == 1:
        albion_guild_info = {
            "Id": apiResponseDict["guilds"][0].get("Id"),
            "Name": apiResponseDict["guilds"][0].get("Name"),
            "AllianceId": apiResponseDict["guilds"][0].get("AllianceId"),
            "Found": True,
        }

    return albion_guild_info


async def apiGuildsInfoProcess(apiResponseDict: dict):
    """
    Process API response dictionary for guilds by extracting relevant information and formatting certain fields.

    Args:
        apiResponseDict (dict): A dictionary containing the raw response data from the Albion Online API.

    Returns:
        dict: A dictionary containing the relevant information extracted from the raw API response, including the guild's
        ID, name, founder ID and name, founding date, alliance tag and ID, kill fame and death fame, member count, and
        whether the guild was found in the API response.
    """

    killFameReadable = millify(apiResponseDict.get("killFame"), precision=2)
    deathFameReadable = millify(apiResponseDict.get("DeathFame"), precision=2)

    albionGuildInfo = {
        "Id": apiResponseDict.get("Id"),
        "Name": apiResponseDict.get("Name"),
        "FounderId": apiResponseDict.get("FounderId"),
        "FounderName": apiResponseDict.get("FounderName"),
        "Founded": apiResponseDict.get("Founded"),
        "AllianceTag": apiResponseDict.get("AllianceTag"),
        "AllianceId": apiResponseDict.get("AllianceId"),
        "KillFame": killFameReadable,
        "DeathFame": deathFameReadable,
        "MemberCount": apiResponseDict.get("MemberCount"),
        "Found": True,
    }

    return albionGuildInfo


async def apiPlayerInfoProcess(apiResponseDict: dict):
    """
    Process API response dictionary for guilds by extracting relevant information and formatting certain fields.

    Args:
        apiResponseDict (dict): A dictionary of player information obtained from the Albion Online API.

    Returns:
        dict: A dictionary of processed player information, including name, ID, guild name and ID, alliance name and ID, death and kill fame, PvP and PvE ratios, fame ratio, and various types of lifetime fame (e.g. total PvE fame, gathering fame, crafting fame, etc.), all of which have been formatted and converted to readable strings.

    """

    PvETotalFame = (
        apiResponseDict.get("LifetimeStatistics", {}).get("PvE", {}).get("Total")
    )
    PvETotalFameFix = millify(PvETotalFame, precision=2)

    PvERoyalFame = (
        apiResponseDict.get("LifetimeStatistics", {}).get("PvE", {}).get("Royal")
    )
    PvERoyalFameFix = millify(PvERoyalFame, precision=2)

    PvEOutlandsFame = (
        apiResponseDict.get("LifetimeStatistics", {}).get("PvE", {}).get("Outlands")
    )
    PvEOutlandsFameFix = millify(PvEOutlandsFame, precision=2)

    PvEAvalonFame = (
        apiResponseDict.get("LifetimeStatistics", {}).get("PvE", {}).get("Avalon")
    )
    PvEAvalonFameFix = millify(PvEAvalonFame, precision=2)

    PvEHellgateFame = (
        apiResponseDict.get("LifetimeStatistics", {}).get("PvE", {}).get("Hellgate")
    )
    PvEHellgateFameFix = millify(PvEHellgateFame, precision=2)

    PvECorruptedDungeonFame = (
        apiResponseDict.get("LifetimeStatistics", {})
        .get("PvE", {})
        .get("CorruptedDungeon")
    )
    PvECorruptedDungeonFameFix = millify(PvECorruptedDungeonFame, precision=2)

    GatheringFiberFame = (
        apiResponseDict.get("LifetimeStatistics", {})
        .get("Gathering", {})
        .get("Fiber", {})
        .get("Total")
    )
    GatheringFiberFameFix = millify(GatheringFiberFame, precision=2)

    GatheringHideFame = (
        apiResponseDict.get("LifetimeStatistics", {})
        .get("Gathering", {})
        .get("Hide", {})
        .get("Total")
    )
    GatheringHideFameFix = millify(GatheringHideFame, precision=2)

    GatheringOreFame = (
        apiResponseDict.get("LifetimeStatistics", {})
        .get("Gathering", {})
        .get("Ore", {})
        .get("Total")
    )
    GatheringOreFameFix = millify(GatheringOreFame, precision=2)

    GatheringWoodFame = (
        apiResponseDict.get("LifetimeStatistics", {})
        .get("Gathering", {})
        .get("Wood", {})
        .get("Total")
    )
    GatheringWoodFameFix = millify(GatheringWoodFame, precision=2)

    Gathering = (
        apiResponseDict.get("LifetimeStatistics", {})
        .get("Gathering", {})
        .get("All", {})
        .get("Total")
    )
    GatheringFameFix = millify(Gathering, precision=2)

    Crafting = (
        apiResponseDict.get("LifetimeStatistics", {}).get("Crafting", {}).get("Total")
    )
    CraftingFameFix = millify(Crafting, precision=2)

    FishingFame = apiResponseDict.get("LifetimeStatistics", {}).get("FishingFame")
    FishingFameFix = millify(FishingFame, precision=2)

    FarmingFame = apiResponseDict.get("LifetimeStatistics", {}).get("FarmingFame")
    FarmingFameFix = millify(FarmingFame, precision=2)

    TotalFame = (
        int(PvETotalFame)
        + int(Gathering)
        + int(Crafting)
        + int(apiResponseDict.get("KillFame"))
        + int(FishingFame)
        + int(FarmingFame)
    )
    TotalFameFix = millify(TotalFame, precision=2)

    try:
        PvERatio = round((int(PvETotalFame) / int(TotalFame)), 2)
    except ZeroDivisionError:
        PvERatio = 0

    try:
        PvPRatio = round((int(apiResponseDict.get("KillFame")) / int(TotalFame)), 2)
    except ZeroDivisionError:
        PvPRatio = 0

    FameRatio = apiResponseDict.get("FameRatio")

    KillFameFix = millify(apiResponseDict.get("KillFame"), precision=2)

    DeathFameFix = millify(apiResponseDict.get("DeathFame"), precision=2)

    CrystalFame = apiResponseDict.get("LifetimeStatistics", {}).get("CrystalLeague")
    CrystalFameFix = millify(CrystalFame, precision=2)

    playerInfoProcessed = {
        "Name": apiResponseDict.get("Name"),
        "Id": apiResponseDict.get("Id"),
        "GuildName": apiResponseDict.get("GuildName"),
        "GuildId": apiResponseDict.get("GuildId"),
        "AllianceName": apiResponseDict.get("AllianceName"),
        "AllianceId": apiResponseDict.get("AllianceId"),
        "AllianceTag": apiResponseDict.get("AllianceTag"),
        "DeathFame": DeathFameFix,
        "KillFame": KillFameFix,
        "FameRatio": FameRatio,
        "PvETotalFame": PvETotalFameFix,
        "PvERoyal": PvERoyalFameFix,
        "PvEOutlands": PvEOutlandsFameFix,
        "Avalon": PvEAvalonFameFix,
        "Hellgate": PvEHellgateFameFix,
        "CorruptedDungeon": PvECorruptedDungeonFameFix,
        "GatheringFiber": GatheringFiberFameFix,
        "GatheringHide": GatheringHideFameFix,
        "GatheringOre": GatheringOreFameFix,
        "GatheringWood": GatheringWoodFameFix,
        "GatheringFame": GatheringFameFix,
        "CraftingFame": CraftingFameFix,
        "FishingFame": FishingFameFix,
        "FarmingFame": FarmingFameFix,
        "TotalFame": TotalFameFix,
        "PvERatio": PvERatio,
        "PvPRatio": PvPRatio,
        "CrystalFame": CrystalFameFix,
        "Found": True,
    }

    return playerInfoProcessed
