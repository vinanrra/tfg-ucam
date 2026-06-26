import nextcord
from functions.aiohttp import albionApi
from functions.checks import check_api_result, check_valid_id
from functions.embebs import Confirm, ao_regions
from functions.mysql import (
    allianceDelete,
    allianceInsert,
    allianceSelect,
    allianceSelectAll,
    settingsSelect,
)
from functions.perms import checkRole, checkRoleAdmin
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, menus

TESTING_GUILD_ID = 419816336768630794  # Replace with your testing guild id


class allianceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        description="Add, remove or list the alliances that are able to register"
    )
    async def alliance(self, interaction: Interaction):
        """
        This is the alliance slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass

    @alliance.subcommand(description="Add a alliance")
    @application_checks.check(checkRoleAdmin)
    async def add(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albionAllianceId: str = SlashOption(
            required=True,
            name="alliance_id",
            description="Alliance ID",
        ),
        allianceRole: nextcord.role.Role = SlashOption(
            required=True,
            name="alliance_role",
            description="Select the rol which this alliance will have it",
        ),
        allianceTag: str = SlashOption(
            required=True,
            name="alliance_tag",
            description="Write the alliance tag maximun 7 characteres",
        ),
    ):
        """
        This is a subcommand of the '/alliance' slash command.
        It will appear in the menu as '/alliance add'.
        """

        await interaction.response.defer()

        discordGuildId = interaction.guild_id
        settings = await settingsSelect(discordGuildId)

        if settings is None:
            embed_settings = nextcord.Embed(
                title="Error:",
                description="Configure first the bot with **/setup config**",
            )
            await interaction.followup.send(embed=embed_settings)
            return

        isValidId, embed_invalid_id = await check_valid_id(albionAllianceId)

        if isValidId is True:
            await interaction.followup.send(embed=embed_invalid_id)
            return

        settings_alliance_tag_lenght: int = int(settings.nickAllyTagLenght)

        if len(allianceTag) > settings_alliance_tag_lenght:
            embed_error = nextcord.Embed(
                title="Error:",
                description=f"{allianceTag} it's longer than {settings_alliance_tag_lenght} characters",
            )
            await interaction.followup.send(embed=embed_error)
            return

        result_api_alliance = await albionApi("alliance", albionAllianceId, region)

        check_api_alliance = await check_api_result(result_api_alliance["Found"])

        if check_api_alliance is not False:
            await interaction.followup.send(
                embed=check_api_alliance,
            )
            return

        embed_alliance = nextcord.Embed(title="Alliance settings:")
        embed_alliance.add_field(
            name="Alliance ID:", value=f"```{albionAllianceId}```", inline=False
        )
        embed_alliance.add_field(
            name="Alliance name:",
            value=f"{result_api_alliance['AllianceName']}",
            inline=False,
        )
        embed_alliance.add_field(
            name="Alliance role:", value=f"<@&{allianceRole.id}>", inline=False
        )
        embed_alliance.add_field(
            name="Alliance Tag:", value=f"[{allianceTag}]", inline=False
        )
        embed_alliance.add_field(
            name="Numbers of players:",
            value=f"{result_api_alliance['NumPlayers']}",
            inline=False,
        )

        view = Confirm()

        await interaction.followup.send(embed=embed_alliance, view=view)
        view.message = await interaction.original_message()
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            await allianceInsert(
                discordGuildId,
                albionAllianceId,
                result_api_alliance["AllianceName"],
                allianceRole.id,
                allianceTag,
                region,
            )
            return
        else:
            return

    @alliance.subcommand(description="Remove a alliance")
    @application_checks.check(checkRoleAdmin)
    async def remove(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albionAllianceId: str = SlashOption(
            required=True,
            name="alliance_id",
            description="Alliance ID",
        ),
    ):
        """
        This is a subcommand of the '/alliance' slash command.
        It will appear in the menu as '/alliance remove'.
        """

        discordGuildId = interaction.guild_id

        alliance_select = await allianceSelect(discordGuildId, albionAllianceId, region)

        if alliance_select != None:
            embed_alliance_delete = nextcord.Embed(title="Delete alliance settings?")
            embed_alliance_delete.add_field(
                name="Alliance ID:",
                value=f"```{alliance_select.albionAllianceId}```",
                inline=False,
            )
            embed_alliance_delete.add_field(
                name="Alliance name:",
                value=f"{alliance_select.albionAllianceName}",
                inline=False,
            )
            embed_alliance_delete.add_field(
                name="Alliance role:",
                value=f"<@&{alliance_select.allianceRole}>",
                inline=False,
            )
            embed_alliance_delete.add_field(
                name="Alliance Tag:",
                value=f"[{alliance_select.allianceTag}]",
                inline=False,
            )

            view = Confirm()

            await interaction.response.send_message(
                embed=embed_alliance_delete, view=view
            )

            view.message = await interaction.original_message()

            await view.wait()

            if view.value is None:
                return
            elif view.value:
                await allianceDelete(discordGuildId, albionAllianceId, region)
                return
            else:
                return

        else:
            embed_alliance_delete = nextcord.Embed(
                title="Alliance not found",
                description=f"This Alliance id **({albionAllianceId})** isn't configure or it's invalid, use **/alliance add** to configure",
            )
            await interaction.response.send_message(embed=embed_alliance_delete)

    @alliance.subcommand(description="Show the alliance details")
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
        albionAllianceId: str = SlashOption(
            required=True,
            name="alliance_id",
            description="Alliance ID",
        ),
    ):
        """
        This is a subcommand of the '/alliance' slash command.
        It will appear in the menu as '/alliance show'.
        """

        discordGuildId = interaction.guild_id

        alliance_select = await allianceSelect(discordGuildId, albionAllianceId, region)

        if alliance_select != None:
            embed_alliance_show = nextcord.Embed(title="Alliance settings:")
            embed_alliance_show.add_field(
                name="Alliance ID:",
                value=f"```{alliance_select.albionAllianceId}```",
                inline=False,
            )
            embed_alliance_show.add_field(
                name="Alliance name:",
                value=f"{alliance_select.albionAllianceName}",
                inline=False,
            )
            embed_alliance_show.add_field(
                name="Alliance role:",
                value=f"<@&{alliance_select.allianceRole}>",
                inline=False,
            )
            embed_alliance_show.add_field(
                name="Alliance Tag:",
                value=f"[{alliance_select.allianceTag}]",
                inline=False,
            )

        else:
            embed_alliance_show = nextcord.Embed(
                title="Alliance not found",
                description="This alliance isn't configure, use **/alliance add** to configure",
            )

        await interaction.response.send_message(embed=embed_alliance_show)

    @alliance.subcommand(description="List all configured alliances")
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
    ):
        """
        This is a subcommand of the '/alliance' slash command.
        It will appear in the menu as '/alliance list'.
        """

        discordGuildId = interaction.guild_id
        resutl_guild_list = await allianceSelectAll(discordGuildId, region)

        class MyEmbedFieldPageSource(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=15)

            async def format_page(self, menu, entries):
                embed = nextcord.Embed(title="Alliance list")
                for entry in entries:
                    embed.add_field(name=entry[0], value=entry[1], inline=False)
                embed.set_footer(
                    text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
                )
                return embed

        async def slash_pages(interaction: nextcord.Interaction):
            fields = []
            for user_obj in resutl_guild_list:
                fields.append((user_obj.albionAllianceName, user_obj.albionAllianceId))
            pages = menus.ButtonMenuPages(
                source=MyEmbedFieldPageSource(fields),
                clear_buttons_after=True,
            )

            await pages.start(interaction=interaction)

        await slash_pages(interaction=interaction)


def setup(bot):
    bot.add_cog(allianceCog(bot))
