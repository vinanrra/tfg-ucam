import logging

import nextcord
from functions.aiohttp import albionApi
from functions.checks import check_api_result, check_valid_id
from functions.embebs import Confirm, ao_regions
from functions.mysql import (
    guildDelete,
    guildInsert,
    guildSelect,
    guildSelectAll,
    registerSelectAllDiscordByGuildName,
    settingsSelect,
)
from functions.perms import checkRole, checkRoleAdmin
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, menus

TESTING_GUILD_ID = 419816336768630794  # Replace with your testing guild id


class guildCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        description="Add, remove or list the guilds that are able to register on this server"
    )
    async def guild(self, interaction: Interaction):
        """
        This is the guild slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass

    @guild.subcommand(description="Add/Edit a guild setting")
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
        albionGuildId: str = SlashOption(
            required=True,
            name="guild_id",
            description="Guild ID",
        ),
        guildRole: nextcord.role.Role = SlashOption(
            required=True,
            name="guild_role",
            description="Select the rol which this guild will have it",
        ),
        guildTag: str = SlashOption(
            required=True,
            name="guild_tag",
            description="Write the guild tag maximun 7 characteres",
        ),
    ):
        """
        This is a subcommand of the '/guild' slash command.
        It will appear in the menu as '/guild add'.
        """

        await interaction.response.defer()

        discordGuildId = interaction.guild_id
        settings = await settingsSelect(discordGuildId)

        if settings == None:
            embed_settings = nextcord.Embed(
                title="No settings found",
                description="Configure first the bot with **/setup config**",
            )
            await interaction.followup.send(embed=embed_settings)
            return

        isValidId, embed_invalid_id = await check_valid_id(albionGuildId)

        if isValidId is True:
            await interaction.followup.send(embed=embed_invalid_id)
            return

        settings_guild_tag_lenght: int = int(settings.nickGuildTagLenght)

        if len(guildTag) > settings_guild_tag_lenght:
            embed_error = nextcord.Embed(
                title="Error:",
                description=f"{guildTag} it's longer than {settings_guild_tag_lenght} characteres",
            )
            await interaction.followup.send(embed=embed_error)
            return

        result_api_guild = await albionApi("guild", albionGuildId, region)

        check_api = await check_api_result(result_api_guild["Found"])

        if check_api != False:
            await interaction.followup.send(
                embed=check_api,
            )
            return

        # Check if guild was found
        try:
            if result_api_guild is None or "Name" not in result_api_guild:
                logging.info(f"Guild ID: {albionGuildId} not found.")
                embed_error = nextcord.Embed(
                    title="Error:", description=f"Guild ID: {albionGuildId} not found"
                )
                await interaction.followup.send(embed=embed_error)
                return
        except TypeError:
            logging.info(f"ERROR - TypeError with {albionGuildId}")
            embed_error = nextcord.Embed(
                title="Error:",
                description=f"There was an error seaching the guild ID: {albionGuildId}",
            )
            await interaction.followup.send(embed=embed_error)
            return

        embed_guild = nextcord.Embed(title="Guild settings:")
        embed_guild.add_field(name="Guild ID:", value=f"{albionGuildId}", inline=False)
        embed_guild.add_field(
            name="Guild name:", value=f"{result_api_guild['Name']}", inline=False
        )
        embed_guild.add_field(
            name="Guild role:", value=f"<@&{guildRole.id}>", inline=False
        )
        embed_guild.add_field(name="Guild Tag:", value=f"[{guildTag}]", inline=False)

        view = Confirm()

        await interaction.followup.send(embed=embed_guild, view=view)
        view.message = await interaction.original_message()
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            await guildInsert(
                discordGuildId,
                albionGuildId,
                result_api_guild["Name"],
                guildRole.id,
                guildTag,
                region,
            )
            return
        else:
            return

    @guild.subcommand(description="Remove a guild")
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
        albionGuildId: str = SlashOption(
            required=True,
            name="guild_id",
            description="Guild ID",
        ),
    ):
        """
        This is a subcommand of the '/guild' slash command.
        It will appear in the menu as '/guild remove'.
        """

        discordGuildId = interaction.guild_id

        guild_select = await guildSelect(discordGuildId, albionGuildId, region)

        if guild_select is not None:
            embed_guild_delete = nextcord.Embed(
                title="Delete guild settings?",
                description=":warning: This also will remove all roles from the users of this guild :warning:",
            )
            embed_guild_delete.add_field(
                name="Guild ID:", value=f"{guild_select.albionGuildId}", inline=False
            )
            embed_guild_delete.add_field(
                name="Guild name:",
                value=f"{guild_select.albionGuildName}",
                inline=False,
            )
            embed_guild_delete.add_field(
                name="Guild role:", value=f"<@&{guild_select.guildRole}>", inline=False
            )
            embed_guild_delete.add_field(
                name="Guild Tag:", value=f"[{guild_select.guildTag}]", inline=False
            )

            view = Confirm()

            await interaction.response.send_message(embed=embed_guild_delete, view=view)

            view.message = await interaction.original_message()
            await view.wait()

            if view.value:
                # Remove perms from users registered with that guild
                discordUserIdList = []
                discordUserNickList = []
                guild = interaction.guild
                guild_registered_users = await registerSelectAllDiscordByGuildName(
                    discordGuildId, guild_select.albionGuildName, region
                )

                for user_obj in guild_registered_users:
                    # Show the users who are going to be removed

                    class MyEmbedFieldPageSource(menus.ListPageSource):
                        def __init__(self, data):
                            super().__init__(data, per_page=15)

                        async def format_page(self, menu, entries):
                            embed = nextcord.Embed(title="Users to remove perms")
                            for entry in entries:
                                embed.add_field(
                                    name=entry[0], value=entry[1], inline=False
                                )
                            embed.set_footer(
                                text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
                            )
                            return embed

                    async def slash_pages(interaction: nextcord.Interaction):
                        fields = []
                        fields.append(
                            (
                                "User info:",
                                f"<@{user_obj.discordUserId}>, {user_obj.registerGuild}",
                            )
                        )
                        pages = menus.ButtonMenuPages(
                            source=MyEmbedFieldPageSource(fields),
                            clear_buttons_after=True,
                        )

                        await pages.start(interaction=interaction)

                    await slash_pages(interaction=interaction)

                    embed_user_confirm = nextcord.Embed(
                        title="Confirm the user list",
                        description=":warning: If the above list it's correct, accept the change :warning:",
                    )

                    view_user_list = Confirm()

                    await interaction.send(
                        embed=embed_user_confirm, view=view_user_list
                    )

                    view_user_list.message = await interaction.original_message()

                    await view_user_list.wait()

                    if view_user_list.value:
                        try:
                            member = await guild.fetch_member(user_obj.discordUserId)
                        except Exception as e:
                            logging.info(f"ERROR - CATCH ME {e}")

                        try:
                            await member.edit(roles=[])
                        except:
                            discordUserIdList.append(f"<@{user_obj.discordUserId}>")
                            pass

                        try:
                            await member.edit(nick=None)
                        except:
                            discordUserNickList.append(f"<@{user_obj.discordUserId}>")
                            pass
                    else:
                        return

                await guildDelete(discordGuildId, albionGuildId, region)

                if discordUserIdList != []:
                    embed_guild_delete.add_field(
                        name="ERROR:",
                        value=f"Unable to delete roles from: {discordUserIdList}",
                        inline=False,
                    )

                if discordUserNickList != []:
                    embed_guild_delete.add_field(
                        name="ERROR:",
                        value=f"Unable to remove nick from: {discordUserNickList}",
                        inline=False,
                    )

                await interaction.edit_original_message(embed=embed_guild_delete)

            else:
                return

        else:
            embed_guild_delete = nextcord.Embed(
                title="Guild not found",
                description=f"This guild id **({albionGuildId})** isn't configure or it's invalid, use **/guild add** to configure",
            )
            await interaction.response.send_message(embed=embed_guild_delete)

    @guild.subcommand(description="Show guild details")
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
        albionGuildId: str = SlashOption(
            required=True,
            name="guild_id",
            description="Guild ID",
        ),
    ):
        """
        This is a subcommand of the '/guild' slash command.
        It will appear in the menu as '/guild show'.
        """

        discordGuildId = interaction.guild_id

        guild_select = await guildSelect(discordGuildId, albionGuildId, region)

        if guild_select != None:
            embed_guild_show = nextcord.Embed(title="Guild settings:")
            embed_guild_show.add_field(
                name="Guild ID:", value=f"{guild_select.albionGuildId}", inline=False
            )
            embed_guild_show.add_field(
                name="Guild name:",
                value=f"{guild_select.albionGuildName}",
                inline=False,
            )
            embed_guild_show.add_field(
                name="Guild role:", value=f"<@&{guild_select.guildRole}>", inline=False
            )
            embed_guild_show.add_field(
                name="Guild Tag:", value=f"[{guild_select.guildTag}]", inline=False
            )

        else:
            embed_guild_show = nextcord.Embed(
                title="Guild not found",
                description=f"This guild id **({albionGuildId})** isn't configure or it's invalid, use **/guild add** to configure",
            )

        await interaction.response.send_message(embed=embed_guild_show)

    @guild.subcommand(description="List all configure guilds")
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
        This is a subcommand of the '/guild' slash command.
        It will appear in the menu as '/guild list'.
        """

        discordGuildId = interaction.guild_id
        resutl_guild_list = await guildSelectAll(discordGuildId, region)

        class MyEmbedFieldPageSource(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=15)

            async def format_page(self, menu, entries):
                embed = nextcord.Embed(title="Guild list")
                for entry in entries:
                    embed.add_field(name=entry[0], value=entry[1], inline=False)
                embed.set_footer(
                    text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
                )
                return embed

        async def slash_pages(interaction: nextcord.Interaction):
            fields = []
            for user_obj in resutl_guild_list:
                fields.append((user_obj.albionGuildName, user_obj.albionGuildId))
            pages = menus.ButtonMenuPages(
                source=MyEmbedFieldPageSource(fields),
                clear_buttons_after=True,
            )

            await pages.start(interaction=interaction)

        await slash_pages(interaction=interaction)


def setup(bot):
    bot.add_cog(guildCog(bot))
