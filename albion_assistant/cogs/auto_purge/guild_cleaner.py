# FEATURE - Add logging to discord channel when a member it's purged
import asyncio
import logging
import time
import traceback

import nextcord
from functions.aiohttp import albionApi
from functions.api_process import apiSearchPlayerProcess, guild_get_members_id
from functions.checks import check_api_result
from functions.mysql import (
    guildAll,
    guildSelect,
    guildSelectAllDiscordIdByGuildId,
    guildSelectAllNames,
    region_select,
    registerDeleteDiscord,
    registerInsert,
    registerSelectAllDiscordByGuildName,
    settingsSelect,
)
from functions.nicks import get_guild_name, replace_names, replace_nickname
from nextcord.ext import commands, tasks


class GuildCleaner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_cleaner.start()

    def cog_unload(self):
        self.guild_cleaner.cancel()

    @tasks.loop(hours=2.0)
    async def guild_cleaner(self):
        try:
            logging.info("AUTO-PURGE - Starting guild cleaner")
            start = time.time()

            regions = await region_select()

            for region in regions:
                # Get unique albion guilds from DB
                guild_select = await guildAll(region.serverRegion)

                # To avoid duplicate checks
                checked_guild_list = []

                # Loop each albion guild
                for guild in guild_select:
                    albionGuildName = guild.albionGuildName
                    albuionGuildId = guild.albionGuildId

                    # Avoid duplicate guilds
                    if albuionGuildId not in checked_guild_list:
                        checked_guild_list.append(albuionGuildId)
                        logging.info(
                            "AUTO-PURGE - Starting with %s - %s",
                            albionGuildName,
                            albuionGuildId,
                        )
                    else:
                        continue

                    # Get member list from Albion API
                    guildUserApi = await albionApi(
                        "guild_members", albuionGuildId, region.serverRegion
                    )

                    # Check if there were results
                    try:
                        if (
                            guildUserApi["Found"] is False
                            or guildUserApi["Found"] == "Error"
                        ):
                            logging.info(
                                "AUTO-PURGE - Failed to get guild members from %s - %s",
                                albionGuildName,
                                albuionGuildId,
                            )
                            continue
                    except TypeError:
                        pass

                    # Parse json and get store members ID to list
                    guildUserList = await guild_get_members_id(guildUserApi)

                    # Get Discord IDs where the guild it's configured
                    discordIdList = await guildSelectAllDiscordIdByGuildId(
                        albuionGuildId, region.serverRegion
                    )

                    # Loop each discord
                    for discord in discordIdList:
                        discordId = int(discord.discordGuildId)

                        # Test discord
                        discordLog = 123
                        discordChannel = 123
                        if discordId == discordLog:
                            try:
                                channel = self.bot.get_channel(discordChannel)
                            except:
                                continue

                        # Get bot settings
                        discordSettings = await settingsSelect(discordId)

                        # Only non public discords
                        if discordSettings.public == 1:
                            continue

                        # Get guild obj
                        try:
                            guild = await self.bot.fetch_guild(discordId)
                        except nextcord.errors.Forbidden as error:
                            # If guild failed to fetch continue to next one
                            logging.info(
                                "AUTO-PURGE - ERROR  - Guild permission denied %s",
                                error,
                            )
                            continue
                        except nextcord.errors.HTTPException as error:
                            logging.info("AUTO-PURGE - ERROR - %s", error)
                            continue

                        # Get all registered members where guild.Name
                        discordAlbionGuildMemberList = (
                            await registerSelectAllDiscordByGuildName(
                                discordId, albionGuildName, region.serverRegion
                            )
                        )

                        # Get configured guilds
                        discordConfiguredGuilds = await guildSelectAllNames(
                            discordId, region.serverRegion
                        )

                        # Compare Member API and registered
                        for registeredMember in discordAlbionGuildMemberList:
                            registerAlbionUserId = registeredMember.albionUserId
                            registerGuildName = registeredMember.registerGuild
                            registerDiscordUserId = registeredMember.discordUserId
                            registerAlbionNick = registeredMember.albionNick

                            if registerAlbionNick is None:
                                logging.info(
                                    "AUTO-PURGE - ERROR - Nick not found: Discord ID: %s -  Albion Nick: %s - Albion ID: %s",
                                    registerDiscordUserId,
                                    registerAlbionNick,
                                    registerAlbionUserId,
                                )
                                continue

                            # If member it's on the guild ignore
                            # If member was manual ignore
                            if (
                                registerAlbionUserId in guildUserList
                                or registerGuildName == "Info: Manual register"
                            ):
                                continue

                            logging.info(
                                "AUTO-PURGE - Found an user not in the guild %s - %s - %s",
                                registerGuildName,
                                registerAlbionNick,
                                registerAlbionUserId,
                            )

                            # Ask API
                            apiResult = await albionApi(
                                "search", registerAlbionNick, region.serverRegion
                            )

                            # Check result
                            checkApiResult = await check_api_result(apiResult["Found"])

                            if checkApiResult is not False:
                                logging.info(
                                    "ERROR - AUTO-PURGE - Unable to find %s",
                                    registerAlbionNick,
                                )
                                continue

                            # Process data
                            apiResultData = await apiSearchPlayerProcess(
                                apiResult, registerAlbionNick
                            )

                            # Check processed data
                            checkProcessedResult = await check_api_result(
                                apiResultData["Found"]
                            )

                            # Check processed data
                            if checkProcessedResult is not False:
                                logging.info(
                                    "ERROR - AUTO-PURGE - Unable to process data of user  %s",
                                    registerAlbionNick,
                                )
                                continue

                            # Check if new guild it's on the registered guild
                            if apiResultData["GuildName"] in discordConfiguredGuilds:
                                # Update user entry with the new guild name from API
                                await registerInsert(
                                    registeredMember.discordGuildId,
                                    registeredMember.discordUserId,
                                    registeredMember.albionUserId,
                                    registeredMember.albionNick,
                                    registeredMember.registerUserId,
                                    registeredMember.registerUserNick,
                                    registeredMember.registerDate,
                                    apiResultData["GuildName"],
                                    registeredMember.registerAlliance,
                                    registeredMember.serverRegionFK,
                                )
                                # Get the tag from the registered guild
                                dbGuildInfo = await guildSelect(
                                    discordId,
                                    apiResultData["GuildId"],
                                    region.serverRegion,
                                )
                                # Update TAG
                                try:
                                    member = await guild.fetch_member(
                                        registerDiscordUserId
                                    )
                                    memberNickOld = member.nick
                                    # Change nickname
                                    memberNickNew = replace_nickname(
                                        memberNickOld,
                                        registeredMember.albionNick,
                                        apiResultData["Name"],
                                    )
                                    # Change guild
                                    guildTag = get_guild_name(
                                        memberNickNew, discordSettings.nickTagOrder
                                    )

                                    if guildTag is not None:
                                        memberNickNew = replace_names(
                                            memberNickOld,
                                            guildTag,
                                            dbGuildInfo.guildTag,
                                        )
                                    # Change alliance, need to be standarized
                                    # memberNickNew = replace_names(
                                    #     memberNickOld,
                                    #     registerGuildName,
                                    #     apiResultData["GuildName"],
                                    # )
                                    if memberNickOld != memberNickNew:
                                        await member.edit(nick=f"{memberNickNew}")
                                        if discordId == discordLog:
                                            await channel.send(
                                                content=f"""**Updated guild/alliance tag:
                                                                    \n**OLD: {memberNickOld} -> NEW: <@{registerDiscordUserId}>
                                                                    \n**Albion Nick:** {registerAlbionNick}
                                                                    \n**Reason:** Moved from guild {registerGuildName} to {apiResultData['GuildName']}"""
                                            )
                                    continue
                                except (nextcord.NotFound, nextcord.Forbidden):
                                    continue
                                except nextcord.HTTPException:
                                    logging.info("ERROR - %s", traceback.format_exc())
                                    continue

                            # Remove form DB
                            await registerDeleteDiscord(
                                discordId,
                                registerDiscordUserId,
                                region.serverRegion,
                            )
                            if discordId == discordLog:
                                # Left guild msg
                                await channel.send(
                                    content=f"""**Removed user:** <@{registerDiscordUserId}>
                                                        \n**Albion Nick:** {registerAlbionNick}
                                                        \n**Reason:** Left guild {registerGuildName}"""
                                )
                            try:
                                member = await guild.fetch_member(registerDiscordUserId)
                                # Purge roles and nick
                                await member.edit(roles=[])
                                await member.edit(nick=None)
                                logging.info(
                                    "AUTO-PURGE - Removed %s - %s, member tag: %s - <%s>",
                                    registerDiscordUserId,
                                    registerAlbionNick,
                                    member,
                                    member.id,
                                )
                                continue
                            except (nextcord.NotFound, nextcord.Forbidden):
                                pass
                            except nextcord.HTTPException:
                                logging.info("ERROR - %s", traceback.format_exc())
                                pass

                            # Left guild msg but failed to remove roles and nick
                            logging.info(
                                "AUTO-PURGE - Removed  %s - %s from %s - %s - ONLY FROM DB",
                                registerDiscordUserId,
                                registerAlbionNick,
                                guild.name,
                                guild.id,
                            )

                end = time.time()
                elapse_time = end - start
                logging.info(
                    "AUTO-PURGE - Finished guild cleaner took  %s", elapse_time
                )
        except:
            logging.info("ERROR - AUTO-PURGE - %s", traceback.format_exc())
            pass

    @guild_cleaner.before_loop
    async def before_guild_cleaner(self):
        logging.info("AUTO-PURGE: Waiting bot to be ready...")
        await asyncio.sleep(600)
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(GuildCleaner(bot))
