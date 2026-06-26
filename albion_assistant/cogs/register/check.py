import nextcord
from functions.aiohttp import albionApi
from functions.api_process import (
    apiGuildsInfoProcess,
    apiSearchGuildProcess,
)
from functions.checks import check_api_result
from functions.embebs import DropdownViewCheck, ao_regions
from nextcord import Interaction, SlashOption
from nextcord.ext import commands


class checkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(description="Get info from Albion Online")
    async def check(self, interaction: Interaction):
        """
        This is the main slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass

    # With ,inherit_hooks = True if you use @main.error should catch all errors from subcommands too
    @check.subcommand(description="Get info from an Albion Online nickname")
    async def user(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albion_nick: str = SlashOption(
            required=True,
            name="albion_nick",
            description="Albion Online username to serach",
        ),
    ):
        """
        This is a subcommand of the '/check' slash command.
        It will appear in the menu as '/check user'.
        """

        await interaction.response.defer()

        # API SEARCH

        albion_nick_lower = albion_nick.lower()

        # Ask API
        apiResult = await albionApi("search", albion_nick_lower, region)

        # Check result
        checkApiResult = await check_api_result(apiResult["Found"])

        if checkApiResult is not False:
            await interaction.followup.send(embed=checkApiResult)
            return

        view = DropdownViewCheck(apiResult, region)

        await interaction.followup.send(view=view)

    @check.subcommand(description="Get info from an Albion Online guild")
    async def guild(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albion_guild_name: str = SlashOption(
            required=True,
            name="albion_guild_name",
            description="Albion Online guild name to serach",
        ),
    ):
        await interaction.response.defer()

        # Ask API
        apiResult = await albionApi("search", albion_guild_name, region)

        # Check result
        checkApiResult = await check_api_result(apiResult["Found"])

        if checkApiResult is not False:
            await interaction.followup.send(embed=checkApiResult)
            return

        # Process data
        apiResultData = await apiSearchGuildProcess(apiResult, albion_guild_name)

        # Check processed data
        checkProcessedResult = await check_api_result(apiResultData["Found"])

        # Check processed data
        if checkProcessedResult is not False:
            await interaction.followup.send(embed=checkProcessedResult)
            return

        # Ask API
        apiResult = await albionApi("guild", apiResultData["Id"], region)

        # Check result
        checkApiResult = await check_api_result(apiResult["Found"])

        if checkApiResult is not False:
            await interaction.followup.send(embed=checkApiResult)
            return

        # Process data
        apiResultData = await apiGuildsInfoProcess(apiResult)

        # Check processed data
        checkProcessedResult = await check_api_result(apiResultData["Found"])

        # Check processed data
        if checkProcessedResult is not False:
            await interaction.followup.send(embed=checkProcessedResult)
            return

        albionOnlineTools = f"https://albiononlinetools.com/player/guild.php?guildID={apiResultData['Id']}&sv={region.lower()}"

        embebCheckGuild = nextcord.Embed(title="Guild Info", color=0x00FF00)
        embebCheckGuild.add_field(
            name="Name", value=apiResultData["Name"], inline=False
        )
        # Show as code at discord
        embebCheckGuild.add_field(
            name="Id", value=f"```{apiResultData['Id']}```", inline=False
        )
        # Show as code at discord
        embebCheckGuild.add_field(
            name="Founder Id", value=f"```{apiResultData['FounderId']}```", inline=False
        )
        embebCheckGuild.add_field(
            name="Founder Name", value=apiResultData["FounderName"], inline=False
        )
        embebCheckGuild.add_field(
            name="Founded", value=apiResultData["Founded"], inline=False
        )
        if apiResultData["AllianceTag"] != "":
            embebCheckGuild.add_field(
                name="Alliance Tag", value=apiResultData["AllianceTag"], inline=False
            )
        if apiResultData["AllianceId"] != "":
            # Show as code at discord
            embebCheckGuild.add_field(
                name="Alliance Id",
                value=f"```{apiResultData['AllianceId']}```",
                inline=False,
            )
        embebCheckGuild.add_field(
            name="Kill Fame", value=apiResultData["KillFame"], inline=False
        )
        embebCheckGuild.add_field(
            name="Death Fame", value=apiResultData["DeathFame"], inline=False
        )
        embebCheckGuild.add_field(
            name="MemberCount", value=apiResultData["MemberCount"], inline=False
        )
        embebCheckGuild.add_field(
            name="More info:",
            value=f"""[AlbionOnlineTools]({albionOnlineTools})""",
        )

        await interaction.followup.send(
            embed=embebCheckGuild,
        )
        return


def setup(bot):
    bot.add_cog(checkCog(bot))
