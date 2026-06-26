import logging
from datetime import datetime

import nextcord
from functions.aiohttp import albionApi
from functions.api_process import (
    apiPlayerInfoProcess,
    apiSearchGuildProcess,
    apiSearchPlayerProcess,
)
from functions.checks import check_api_result, check_valid_id
from functions.embebs import Confirm, ao_regions, donations_name, donations_value
from functions.mysql import (
    blacklistDelete,
    blacklistDeleteByTypeName,
    blacklistInsert,
    blacklistSelectAll,
    blacklistSelectAllByType,
    blacklistSelectByType,
    blacklistSelectId,
    registerSelect,
    settingsSelect,
)
from functions.mysql_conversion import blacklistTypeToString
from functions.perms import checkRole
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, menus


class blacklistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(description="Manage blacklist")
    async def blacklist(self, interaction: Interaction):
        """
        This is the main slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass

    @blacklist.subcommand(description="Add user/guild/alliance to blacklist")
    @application_checks.check(checkRole)
    # FEATURE - Check if user it's blacklisted and if it's ask if he wants to update the entry
    async def add(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        blacklistName: str = SlashOption(
            required=True,
            name="name",
            description="Albion Online user/guild/name to search",
        ),
        blacklist_reason: str = SlashOption(
            required=True,
            name="reason",
            description="Reason why the user/guild/alliance has been blacklisted",
        ),
        blacklist_type: int = SlashOption(
            required=True,
            name="type",
            description="What are you gonna blacklist?",
            choices={
                "User": 1,
                "Guild": 2,
                "Alliance": 3,
            },
        ),
        blacklist_id: str = SlashOption(
            required=False,
            name="albion_online_id",
            description="The Albion Online ID to blacklist, using this, will ignore the parameter 'name'",
            default=None,
        ),
    ):
        """
        This is a subcommand of the '/blacklist' slash command.
        It will appear in the menu as '/blacklist add'.
        """

        await interaction.response.defer()

        discordGuildId = interaction.guild_id
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        blacklistById = interaction.user.id
        blacklistByNickname = interaction.user.name

        settings = await settingsSelect(discordGuildId)

        if settings is None:
            embed_settings = nextcord.Embed(
                title="No settings found",
                description="Configure first the bot with **/setup config**",
            )
            await interaction.followup.send(embed=embed_settings)
            return

        if len(blacklist_reason) > 150:
            embed_blacklistreason = nextcord.Embed(
                title="Reason too long", description="The maximum characters are 150"
            )
            await interaction.followup.send(embed=embed_blacklistreason)
            return

        if blacklist_type == 1:
            if blacklist_id is None:
                # Ask API
                apiResult = await albionApi("search", blacklistName.lower(), region)

                # Check result
                checkApiResult = await check_api_result(apiResult["Found"])

                if checkApiResult is not False:
                    await interaction.followup.send(
                        embed=checkApiResult,
                    )
                    return

                # Process data
                albion_api_nick = await apiSearchPlayerProcess(
                    apiResult, blacklistName.lower()
                )

                # Check processed data
                checkProcessedResult = await check_api_result(albion_api_nick["Found"])

                # Check processed data
                if checkProcessedResult is not False:
                    await interaction.followup.send(
                        embed=checkProcessedResult,
                    )
                    return

                blacklist_id = albion_api_nick["Id"]

                # API PLAYER ID SEARCH #

                # Ask API
                apiResult = await albionApi("player", blacklist_id, region)

                # Check result
                checkApiResult = await check_api_result(apiResult["Found"])

                if checkApiResult is not False:
                    await interaction.followup.send(
                        embed=checkApiResult,
                    )
                    return

                # Process data
                apiResultData = await apiPlayerInfoProcess(apiResult)

                # Check processed data
                checkProcessedResult = await check_api_result(apiResultData["Found"])

            else:
                isValidId, embed_invalid_id = await check_valid_id(blacklist_id)

                if isValidId is True:
                    await interaction.followup.send(embed=embed_invalid_id)
                    return
                # API PLAYER ID SEARCH #

                # Ask API
                apiResult = await albionApi("player", blacklist_id, region)

                # Check result
                checkApiResult = await check_api_result(apiResult["Found"])

                if checkApiResult is not False:
                    await interaction.followup.send(
                        embed=checkApiResult,
                    )
                    return

                # Process data
                apiResultData = await apiPlayerInfoProcess(apiResult)

                # Check processed data
                checkProcessedResult = await check_api_result(apiResultData["Found"])

            # Check processed data
            if checkProcessedResult is not False:
                await interaction.followup.send(
                    embed=checkProcessedResult,
                )
                return

            blacklist_name = apiResultData["Name"]
            blacklist_type_converted = "User"

        elif blacklist_type == 2:
            if blacklist_id is None:
                # Ask API
                apiResult = await albionApi("search", blacklistName, region)

                # Check result
                checkApiResult = await check_api_result(apiResult["Found"])

                if checkApiResult is not False:
                    await interaction.followup.send(
                        embed=checkApiResult,
                    )
                    return

                # Process data
                apiResultData = await apiSearchGuildProcess(apiResult, blacklistName)

                # Check processed data
                checkProcessedResult = await check_api_result(apiResultData["Found"])

                # Check processed data
                if checkProcessedResult is not False:
                    await interaction.followup.send(
                        embed=checkProcessedResult,
                    )
                    return

                blacklist_id = apiResultData["Id"]
                result_api = await albionApi("guild", blacklist_id, region)

            else:
                isValidId, embed_invalid_id = await check_valid_id(blacklist_id)

                if isValidId is True:
                    await interaction.followup.send(embed=embed_invalid_id)
                    return

                result_api = await albionApi("guild", blacklist_id, region)

            if result_api is False:
                embed_api_error = nextcord.Embed(
                    title="Error",
                    description="Guild ID not found, get the guild ID with /check guild",
                )
                await interaction.followup.send(
                    embed=embed_api_error,
                )
                return

            else:
                blacklist_name = result_api["Name"]
                blacklist_type_converted = "Guild"

        else:
            if blacklist_id is None:
                embed_api_error = nextcord.Embed(
                    title="Error",
                    description="To blacklist an Alliance you need to provide the ID",
                )
                await interaction.followup.send(
                    embed=embed_api_error,
                )
                return

            result_api = await albionApi("alliance", blacklist_id, region)

            check_api_alliance = await check_api_result(result_api["Found"])

            if check_api_alliance is not False:
                await interaction.followup.send(
                    embed=check_api_alliance,
                )
                return

            blacklist_name = result_api["AllianceName"]
            blacklist_type_converted = "Alliance"

        embed_blacklist_confirm = nextcord.Embed(title="Confirmation")
        embed_blacklist_confirm.add_field(
            name="ID to blacklist:", value=f"```{blacklist_id}```"
        )
        embed_blacklist_confirm.add_field(
            name=f"{blacklist_type_converted}", value=blacklist_name
        )
        embed_blacklist_confirm.add_field(name="Type:", value=blacklist_type_converted)
        embed_blacklist_confirm.add_field(name="Reason:", value=blacklist_reason)
        embed_blacklist_confirm.add_field(
            name=donations_name, value=donations_value, inline=False
        )

        view = Confirm()

        await interaction.followup.send(
            embed=embed_blacklist_confirm,
            view=view,
        )

        view.message = await interaction.original_message()
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            discordGuildId = interaction.guild_id
            await blacklistInsert(
                discordGuildId,
                blacklist_id,
                blacklist_name.lower(),
                dt_string,
                blacklistById,
                blacklistByNickname,
                blacklist_type,
                blacklist_reason,
                region,
            )
            memberregisterInfo = await registerSelect(
                interaction.guild_id, blacklist_name, region
            )

            embed_blacklist_confirm = nextcord.Embed(
                title=f"{blacklist_type_converted} - {blacklist_name} added to blacklist",
                color=0x00FF00,
            )

            if memberregisterInfo:
                memberDiscordId = memberregisterInfo.discordUserId
                guild = interaction.guild
                member = await guild.fetch_member(memberDiscordId)
                try:
                    await member.edit(roles=[], nick=None)
                except nextcord.errors.Forbidden:
                    embed_blacklist_confirm.add_field(
                        name="Failed to remove role:",
                        value="Missing permissions, **Manage role**, if the user it's an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be removed, make sure it is above the roles you want to remove",
                        inline=False,
                    )
                except Exception as e:
                    logging.error(
                        f"Error occurred while trying to remove roles for {member.name}. Error: {e}"
                    )
                    embed_blacklist_confirm.add_field(
                        name="Failed to remove role:",
                        value=f"An error occurred while trying to remove roles for {member.name}",
                        inline=False,
                    )
            await interaction.edit_original_message(embed=embed_blacklist_confirm)
            return
        else:
            return

    @blacklist.subcommand(description="Remove user/guild/alliance from blacklist")
    @application_checks.check(checkRole)
    async def remove(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        blacklistName: str = SlashOption(
            required=True,
            name="name",
            description="Albion Online user/guild/name to search",
        ),
        blacklist_type: int = SlashOption(
            required=True,
            name="type",
            description="Filter by User/Guild/Alliance",
            choices={
                "User": 1,
                "Guild": 2,
                "Alliance": 3,
            },
        ),
        blacklist_id: str = SlashOption(
            required=False,
            name="albion_online_id",
            description="The Albion Online ID of the user/guild/alliance to blacklist",
            default=None,
        ),
    ):
        """
        This is another subcommand of the '/blacklist' slash command.
        It will appear in the menu as '/blacklist remove'.
        """

        discordGuildId = interaction.guild_id

        embed_blacklist_remove = nextcord.Embed(title="Confirmation")
        embed_blacklist_remove.add_field(name="Name:", value=blacklistName)
        if blacklist_id is not None:
            embed_blacklist_remove.add_field(
                name="ID to unblacklist:", value=f"```{blacklist_id}```"
            )

        view = Confirm()

        await interaction.response.send_message(
            embed=embed_blacklist_remove,
            view=view,
        )

        view.message = await interaction.original_message()

        # Wait user confirmation
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            # Remove registration
            try:
                if blacklist_id is not None:
                    await blacklistDelete(discordGuildId, blacklist_id, region)
                else:
                    await blacklistDeleteByTypeName(
                        discordGuildId, blacklist_type, blacklistName.lower(), region
                    )
            except Exception as e:
                embed_sql_errors = nextcord.Embed(title="Error")
                embed_sql_errors.add_field(
                    name="Database error:",
                    value="There was an error with the database please inform at the [Support Server](https://discord.gg/wxaqGTZWXS)",
                    inline=False,
                )
                await interaction.edit_original_message(embed=embed_sql_errors)
                logging.info(e)
                return
        else:
            return

    @blacklist.subcommand(
        description="Show user/guild/alliance blacklist info, if blacklisted"
    )
    @application_checks.check(checkRole)
    async def show(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        blacklistType: int = SlashOption(
            required=True,
            name="type",
            description="Blacklist type to search",
            choices={
                "User": 1,
                "Guild": 2,
                "Alliance": 3,
            },
        ),
        blacklistName: str = SlashOption(
            required=True,
            name="name",
            description="Albion Online user/guild/name to search",
        ),
        albionOnlineId: str = SlashOption(
            required=False,
            name="albion_id",
            description="Albion Online ID of the User/Guild/Alliance",
            default=None,
        ),
    ):
        """
        This is another subcommand of the '/blacklist' slash command.
        It will appear in the menu as '/blacklist show'.
        """
        discordGuildId = interaction.guild_id

        if albionOnlineId is not None:
            blacklist_select = await blacklistSelectId(
                discordGuildId, albionOnlineId, region
            )
        else:
            blacklist_select = await blacklistSelectByType(
                discordGuildId, blacklistName, blacklistType, region
            )

        if blacklist_select is not None:
            blacklistTypeConverted = await blacklistTypeToString(blacklistType)
            embed_blacklisted = nextcord.Embed(
                title=f"Info of the {blacklistTypeConverted.lower()} blacklisted"
            )
            embed_blacklisted.add_field(
                name="ID:", value=f"```{blacklist_select.blacklistId}```", inline=False
            )
            embed_blacklisted.add_field(
                name="Albion Online Name:",
                value=blacklist_select.blacklistAOName,
                inline=False,
            )
            embed_blacklisted.add_field(
                name="Date:", value=blacklist_select.blacklistDate, inline=False
            )
            embed_blacklisted.add_field(
                name="Blacklisted by:",
                value=f"{blacklist_select.blacklistByNickname} - <@{blacklist_select.blacklistById}>",
                inline=False,
            )
            embed_blacklisted.add_field(
                name="Reason:", value=blacklist_select.blacklistReason, inline=False
            )
            await interaction.response.send_message(
                embed=embed_blacklisted,
            )
            return
        else:
            blacklistTypeConverted = await blacklistTypeToString(blacklistType)
            embed_not_blacklisted = nextcord.Embed(
                title=f"Blacklisted {blacklistTypeConverted.lower()} not found"
            )
            embed_not_blacklisted.add_field(name="Name:", value=blacklistName)
            if albionOnlineId is not None:
                embed_not_blacklisted.add_field(
                    name="ID:", value=f"```{albionOnlineId}```"
                )
            embed_not_blacklisted.add_field(
                name="Info:",
                value="If you are unable to find the blacklisted user, try adding the albion_id option",
                inline=False,
            )
            await interaction.response.send_message(
                embed=embed_not_blacklisted,
            )
            return

    @blacklist.subcommand(description="List all users/guilds/alliances blacklisted")
    @application_checks.check(checkRole)
    async def list(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        blacklistType: int = SlashOption(
            required=True,
            name="type",
            description="Albion Online ID of the User/Guild/Alliance",
            choices={"User": 1, "Guild": 2, "Alliance": 3, "All": 4},
        ),
    ):
        """
        This is another subcommand of the '/blacklist' slash command.
        It will appear in the menu as '/blacklist list'.
        """
        discordGuildId = interaction.guild_id
        if blacklistType == 4:
            resutl_blacklist_list = await blacklistSelectAll(discordGuildId, region)
        else:
            resutl_blacklist_list = await blacklistSelectAllByType(
                discordGuildId, blacklistType, region
            )

        class MyEmbedFieldPageSource(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=15)

            async def format_page(self, menu, entries):
                embed = nextcord.Embed(title="Blacklist list")
                for entry in entries:
                    embed.add_field(name=entry[0], value=entry[1], inline=False)
                embed.set_footer(
                    text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
                )
                return embed

        async def slash_pages(interaction: nextcord.Interaction):
            fields = []
            for user_obj in resutl_blacklist_list:
                fields.append((user_obj.blacklistAOName, user_obj.blacklistDate))
            pages = menus.ButtonMenuPages(
                source=MyEmbedFieldPageSource(fields),
                clear_buttons_after=True,
            )

            await pages.start(interaction=interaction)

        await slash_pages(interaction=interaction)


def setup(bot):
    bot.add_cog(blacklistCog(bot))
