import logging
from datetime import datetime

import nextcord
from functions.aiohttp import albionApi
from functions.api_process import apiPlayerInfoProcess, apiSearchPlayerProcess
from functions.checks import check_api_result, check_articles, check_valid_id
from functions.embebs import Confirm, ao_regions, donations_name, donations_value
from functions.mysql import (
    allianceSelectAll,
    blacklistSelectAll,
    guildSelectAll,
    registerDeleteAlbionNick,
    registerDeleteAll,
    registerDeleteDiscord,
    registerInsert,
    registerSelect,
    registerSelectAll,
    registerSelectDiscord,
    settingsSelect,
)
from functions.mysql_conversion import blacklistTypeToString
from functions.perms import checkRole, checkRoleAdmin
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands, menus


class register(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(
        description="Add/Remove/Force/List/Show register/unregister your Albion Nick"
    )
    async def register(self, interaction: Interaction):
        """
        This is the main slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass

    @register.subcommand(description="Register your Albion Online nickname")
    async def start(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albionNick: str = SlashOption(
            required=True,
            name="albion_nick",
            description="Albion Online ingame nickname",
        ),
    ):
        """
        This is a subcommand of the '/register' slash command.
        It will appear in the menu as '/register add'.
        """

        await interaction.response.defer()

        albionNick_lower = albionNick.lower()
        discordGuildId = interaction.guild_id
        register_check = await registerSelect(discordGuildId, albionNick_lower, region)

        # Check if discord it's configured, get tags and order
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.followup.send(
                embed=embed_settings_error,
            )
            return

        # Check if nickname already registered
        if register_check is not None:
            embed_register_registered = nextcord.Embed(
                title="User it's already registered",
                description=f"The user **{albionNick_lower}** it's already registered.\n If you think this it's an error contact with an admin of this Discord.",
            )
            await interaction.followup.send(
                embed=embed_register_registered,
            )
            return

        # Check if discord user by ID it's already registered
        register_check_discord = await registerSelectDiscord(
            discordGuildId, interaction.user.id, region
        )
        if register_check_discord is not None:
            embed_register_registered = nextcord.Embed(
                title="You discord account it's already registered"
            )
            embed_register_registered.add_field(
                name="Registered Albion Online nick:",
                value=f"{register_check_discord.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="**Info:**",
                value="You can unregister your account with: /register remove",
            )
            await interaction.followup.send(
                embed=embed_register_registered,
            )
            return

        # Call API
        # Ask API
        apiResult = await albionApi("search", albionNick_lower, region)

        # Check result
        checkApiResult = await check_api_result(apiResult["Found"])

        if checkApiResult is not False:
            await interaction.followup.send(
                embed=checkApiResult,
            )
            return

        # Process data
        albion_api_nick = await apiSearchPlayerProcess(apiResult, albionNick_lower)

        # Check processed data
        checkProcessedResult = await check_api_result(albion_api_nick["Found"])

        # Check processed data
        if checkProcessedResult is not False:
            await interaction.followup.send(
                embed=checkProcessedResult,
            )
            return

        # Check blacklist
        register_check_blacklist = await blacklistSelectAll(discordGuildId, region)

        if register_check_blacklist is not None:
            blacklisted = False
            for user_obj in register_check_blacklist:
                blacklistType = user_obj.blacklistType
                blacklistReason = user_obj.blacklistReason
                if user_obj.blacklistId in (
                    albion_api_nick["Id"],
                    albion_api_nick["GuildId"],
                    albion_api_nick["AllianceId"],
                ):
                    blacklisted = True
                    break

        if blacklisted:
            blacklistTypeConverted = await blacklistTypeToString(int(blacklistType))
            embed_register_blacklisted = nextcord.Embed(
                title=f"You Albion Online {blacklistTypeConverted.lower()} it's blacklisted"
            )
            embed_register_blacklisted.add_field(
                name="Info:",
                value="If you think this is an error, contact with the admins of the Discord guild",
                inline=False,
            )
            embed_register_blacklisted.add_field(
                name="Reason:", value=f"{blacklistReason}", inline=False
            )
            await interaction.followup.send(
                embed=embed_register_blacklisted,
            )
            return

        roles_id = []

        # Check if guild it's configured
        guild_Select = await guildSelectAll(discordGuildId, region)

        guild_tag = ""
        guild = False
        if guild_Select is not None:
            for user_obj in guild_Select:
                if user_obj.albionGuildId == albion_api_nick["GuildId"]:
                    guild_tag = "[" + user_obj.guildTag + "]"
                    roles_id.append(user_obj.guildRole)
                    guild_name = user_obj.albionGuildName
                    guild = True
                    break

        if not guild:
            guild_tag = ""
            guild_name = "Info: Registered with Alliance"

        # Check if alliance it's configured
        alliance_select = await allianceSelectAll(discordGuildId, region)

        alliance_tag = ""
        alliance = False
        if alliance_select is not None:
            for user_obj in alliance_select:
                if user_obj.albionAllianceId == albion_api_nick["AllianceId"]:
                    alliance_tag = "[" + user_obj.allianceTag + "]"
                    roles_id.append(user_obj.allianceRole)
                    alliance_name = user_obj.albionAllianceName
                    alliance = True
                    break

        if not alliance:
            alliance_tag = ""
            alliance_name = "Info: Registered with Guild"

        if (alliance is False) and (guild is False) and settings.public != 1:
            embed_register_fail = nextcord.Embed(
                title="User not found at guild or alliance"
            )
            embed_register_fail.add_field(
                name=":warning: More info",
                value="""Use `/check user` to check if there are multiple results and register using also the albion id.
                    **Example:**
                        ```/register start albion_region: Americas albion_nick: Queenmirna albion_id: w4YxWAXNTS-u50fqEvmVvw```

                If you think this it's an error contact with an admin of this Discord and they will manually register you, if the problem persist contact with [Support Server](https://discord.gg/wxaqGTZWXS)""",
                inline=False,
            )
            await interaction.followup.send(
                embed=embed_register_fail,
            )
            return

        if settings.public == 1:
            roles_id.append(settings.publicRole)

        if (settings.public == 1) or (alliance is True and guild_tag == ""):
            guild_api_info = await albionApi(
                "guild", albion_api_nick["GuildId"], region
            )

            # Get TAG lenght Guild and Ally
            if alliance_tag == "" and settings.public == 1:
                guild_name = "Info: Public Discord"
                settings_alliance_tag_lenght = settings.nickAllyTagLenght
                # GET ALLIANCE TAG
                if albion_api_nick["AllianceId"] != "":
                    alliance_tag_full = guild_api_info["AllianceTag"]
                    alliance_tag_full_fixed = await check_articles(alliance_tag_full)
                    alliance_tag = (
                        "["
                        + alliance_tag_full_fixed[0:settings_alliance_tag_lenght]
                        + "]"
                    )
                else:
                    alliance_tag = ""

            if guild_tag == "":
                alliance_name = "Info: Public Discord"
                settings_guild_tag_lenght = settings.nickGuildTagLenght
                if albion_api_nick["GuildId"] != "":
                    guild_tag_full = guild_api_info["Name"]
                    guild_tag_full_fixed = await check_articles(guild_tag_full)
                    guild_tag = (
                        "[" + guild_tag_full_fixed[0:settings_guild_tag_lenght] + "]"
                    )
                else:
                    guild_tag = ""

        nickTagOrder = settings.nickTagOrder
        nickGuildTag = settings.nickGuildTag
        nickAllyTag = settings.nickAllyTag

        # Enable/disable tags depending of settings
        if nickGuildTag == 1:
            if not alliance:
                guild_tag = ""
        elif nickGuildTag == 2:
            if not guild:
                guild_tag = ""
        elif nickGuildTag == 4:
            guild_tag = ""

        if nickAllyTag == 1:
            if not alliance:
                alliance_tag = ""
        elif nickAllyTag == 2:
            if not guild:
                alliance_tag = ""
        elif nickAllyTag == 4:
            alliance_tag = ""

        # Show guild tag (yes/no) and alliance tag (yes/no)
        if nickTagOrder == 1:
            new_nick_value = f"{alliance_tag} {guild_tag} {albion_api_nick['Name']}"
        elif nickTagOrder == 2:
            new_nick_value = f"{guild_tag} {alliance_tag} {albion_api_nick['Name']}"

        embed_register_add = nextcord.Embed(title="Registration Info:")
        embed_register_add.add_field(
            name="Albion Online nickname:",
            value=f"{albion_api_nick['Name']}",
            inline=False,
        )
        embed_register_add.add_field(
            name="Albion Online ID:", value=f"{albion_api_nick['Id']}", inline=False
        )
        if albion_api_nick["GuildName"] != "":
            embed_register_add.add_field(
                name="Guild:", value=f"{albion_api_nick['GuildName']}", inline=False
            )
        if albion_api_nick["GuildId"] != "":
            embed_register_add.add_field(
                name="Guild ID:", value=f"{albion_api_nick['GuildId']}", inline=False
            )
        if albion_api_nick["AllianceName"] != "":
            embed_register_add.add_field(
                name="Alliance:",
                value=f"{albion_api_nick['AllianceName']}",
                inline=False,
            )
        if albion_api_nick["AllianceId"] != "":
            embed_register_add.add_field(
                name="Alliance ID:",
                value=f"{albion_api_nick['AllianceId']}",
                inline=False,
            )
        for role_id in roles_id:
            embed_register_add.add_field(
                name="Rol added:", value=f"<@&{role_id}>", inline=False
            )
        embed_register_add.add_field(
            name="New nick:", value=new_nick_value, inline=False
        )
        embed_register_add.add_field(
            name=donations_name, value=donations_value, inline=False
        )

        await interaction.followup.send(
            embed=embed_register_add,
        )

        registered_with_error = False
        # Add role
        for role_id in roles_id:
            try:
                role = interaction.guild.get_role(int(role_id))
            except Exception:
                embed_register_add.add_field(
                    name="Failed to add role:",
                    value=f"Role <@{role_id}> not found, make sure the role exist",
                    inline=False,
                )
                registered_with_error = True
                pass

            if role is None:
                embed_register_add.add_field(
                    name="Failed to add role:",
                    value=f"Role <@{role_id}> not found, make sure the role exist",
                    inline=False,
                )
                registered_with_error = True
            else:
                try:
                    await interaction.user.add_roles(role)
                except nextcord.errors.Forbidden:
                    embed_register_add.add_field(
                        name="Failed to add role:",
                        value="Missing permissions, ** Manage role **, if you are an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be assigned, make sure it is above the roles you want to assign",
                        inline=False,
                    )
                    registered_with_error = True
                    pass
                except nextcord.errors.NotFound:
                    embed_register_add.add_field(
                        name="Failed to add role:",
                        value="Role not found, check if the role exist",
                        inline=False,
                    )
                    registered_with_error = True
                    pass
        # Change nick
        try:
            if settings.editNick == 1:
                new_nick_value = new_nick_value[0:32]
                await interaction.user.edit(nick=new_nick_value)
        except nextcord.errors.Forbidden:
            embed_register_add.add_field(
                name="Failed to change nickname:",
                value="Missing permissions, ** Manage Nicknames **, if you are an admin it may be that the bot does not have permission to edit nicknames to admins, but to basic users.",
                inline=False,
            )
            registered_with_error = True
            pass

        if registered_with_error:
            await interaction.edit_original_message(embed=embed_register_add)

        # Get current date DD-MM-YYYY HH-MM-SS
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        # Add user to DB
        try:
            await registerInsert(
                discordGuildId,
                interaction.user.id,
                albion_api_nick["Id"],
                albion_api_nick["Name"],
                interaction.user.id,
                interaction.user.name,
                dt_string,
                guild_name,
                alliance_name,
                region,
            )
            return
        except Exception as e:
            embed_sql_errors = nextcord.Embed(title="Error")
            embed_sql_errors.add_field(
                name="Database error:",
                value="There was an error with the database please inform at the [Support Server](https://discord.gg/wxaqGTZWXS)",
                inline=False,
            )
            await interaction.response.edit_message(embed=embed_sql_errors)
            logging.info(e)
            return

    @register.subcommand(description="Show registered Albion Online nickname")
    async def show(
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
        This is another subcommand of the '/register' slash command.
        It will appear in the menu as '/register show'.
        """

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.response.send_message(
                embed=embed_settings_error,
            )
            return

        # Check if discord user by ID it's already registered
        register_check_discord = await registerSelectDiscord(
            discordGuildId, interaction.user.id, region
        )

        if register_check_discord is not None:
            embed_register_registered = nextcord.Embed(title="Registration info:")
            embed_register_registered.add_field(
                name="Albion Online nick:",
                value=f"{register_check_discord.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Albion Online ID:",
                value=f"{register_check_discord.albionUserId}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Discord User:",
                value=f"<@{register_check_discord.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registered by:",
                value=f"{register_check_discord.registerUserNick} - <@{register_check_discord.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration date:",
                value=f"{register_check_discord.registerDate}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration guild:",
                value=f"{register_check_discord.registerGuild}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration alliance:",
                value=f"{register_check_discord.registerAlliance}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="**Info:**",
                value="You can unregister your account with: /register remove",
            )
            embed_register_registered.add_field(
                name=donations_name, value=donations_value, inline=False
            )
            await interaction.response.send_message(
                embed=embed_register_registered,
            )
            return
        else:
            embed_register_not_registered = nextcord.Embed(
                title="Error", description="Your account isn't registered"
            )
            embed_register_not_registered.add_field(
                name="**Info:**",
                value="You can register your account with: /register start",
            )
            await interaction.response.send_message(
                embed=embed_register_not_registered,
            )
            return

    @register.subcommand(description="Remove your registered Albion Online nickname")
    async def remove(
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
        This is another subcommand of the '/register' slash command.
        It will appear in the menu as '/register show'.
        """

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.response.send_message(
                embed=embed_settings_error,
            )
            return

        # Check if discord user by ID it's already registered
        register_check_discord = await registerSelectDiscord(
            discordGuildId, interaction.user.id, region
        )

        view = Confirm()

        if register_check_discord is not None:
            embed_register_registered = nextcord.Embed(title="Confirm deletion:")
            embed_register_registered.add_field(
                name="Albion Online nick:",
                value=f"{register_check_discord.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Albion Online ID:",
                value=f"{register_check_discord.albionUserId}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registered by:",
                value=f"{register_check_discord.registerUserNick} - <@{register_check_discord.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration date:",
                value=f"{register_check_discord.registerDate}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Guild:",
                value=f"{register_check_discord.registerGuild}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Alliance:",
                value=f"{register_check_discord.registerAlliance}",
                inline=False,
            )
            embed_register_registered.add_field(
                name=donations_name, value=donations_value, inline=False
            )

            await interaction.response.send_message(
                embed=embed_register_registered, view=view
            )
        else:
            embed_register_not_registered = nextcord.Embed(
                title="Error", description="Your account isn't registered"
            )
            embed_register_not_registered.add_field(
                name="**Info:**",
                value="You can register your account with: /register start",
            )

            await interaction.response.send_message(
                embed=embed_register_not_registered,
            )
            return

        view.message = await interaction.original_message()

        # Wait user confirmation
        await view.wait()

        if view.value:
            edit_errors = False
            embed_edit_errors = nextcord.Embed(title="Error")
            # Remove nick
            try:
                await interaction.user.edit(nick=None)
            except nextcord.errors.Forbidden:
                embed_edit_errors.add_field(
                    name="Missing permissions:",
                    value="**Manage nicknames**, if you are an admin it may be that the bot does not have permissions to edit your nicnkanme",
                    inline=False,
                )
                edit_errors = True
                pass

            # Remove roles
            try:
                await interaction.user.edit(roles=[])
            except nextcord.errors.Forbidden:
                embed_edit_errors.add_field(
                    name="Missing permissions:",
                    value="**Manage role**, if you are an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be assigned, make sure it is above the roles you want to assign",
                    inline=False,
                )
                edit_errors = True
                pass
            except nextcord.errors.NotFound:
                pass

            # Remove nick
            try:
                await interaction.user.edit(nick=None)
            except nextcord.errors.Forbidden:
                embed_edit_errors.add_field(
                    name="Missing permissions:",
                    value="**Manage nicknames**, if you are an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be assigned, make sure it is above the roles you want to assign",
                    inline=False,
                )
                edit_errors = True
                pass
            except nextcord.errors.NotFound:
                pass

            # Remove database entry
            try:
                await registerDeleteDiscord(discordGuildId, interaction.user.id, region)
            except Exception as e:
                embed_edit_errors.add_field(
                    name="**Database**:",
                    value="There was an error with the database please inform at the [Support Server](https://discord.gg/wxaqGTZWXS)",
                    inline=False,
                )
                logging.info(e)
                return
            if edit_errors:
                await interaction.edit_original_message(embed=embed_edit_errors)
        else:
            return

    @register.subcommand(
        description="Check if an user it's registered and show the info"
    )
    @application_checks.check(checkRole)
    async def check(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        discordMember: nextcord.Member = SlashOption(
            required=True,
            name="discord_member",
            description="Albion Online ingame nickname",
        ),
    ):
        """
        This is another subcommand of the '/register' slash command.
        It will appear in the menu as '/register show'.
        """

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.response.send_message(
                embed=embed_settings_error,
            )
            return

        # Check if discord user by ID it's already registered
        register_check_discord = await registerSelectDiscord(
            discordGuildId, discordMember.id, region
        )
        if register_check_discord is not None:
            embed_register_registered = nextcord.Embed(title="Registration info:")
            embed_register_registered.add_field(
                name="Albion Online nick:",
                value=f"{register_check_discord.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Albion Online ID:",
                value=f"{register_check_discord.albionUserId}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Discord User:",
                value=f"<@{register_check_discord.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registered by:",
                value=f"{register_check_discord.registerUserNick} - <@{register_check_discord.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration date:",
                value=f"{register_check_discord.registerDate}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration guild:",
                value=f"{register_check_discord.registerGuild}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registration alliance:",
                value=f"{register_check_discord.registerAlliance}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="**Info:**",
                value="You can unregister this account with: /register manual deletion",
            )
            embed_register_registered.add_field(
                name=donations_name, value=donations_value, inline=False
            )
            await interaction.response.send_message(
                embed=embed_register_registered,
            )
            return
        else:
            embed_register_not_registered = nextcord.Embed(
                title="Error", description="This account isn't registered"
            )
            embed_register_not_registered.add_field(
                name="**Info:**",
                value="You can register this account with: /register manual addition",
            )
            await interaction.response.send_message(
                embed=embed_register_not_registered,
            )
            return

    @register.subcommand(
        description="List all registered users ordered by Albion Online Nick"
    )
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
        This is another subcommand of the '/register' slash command.
        It will appear in the menu as '/register list'.
        """

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.response.send_message(
                embed=embed_settings_error,
            )
            return

        resutl_register_list = await registerSelectAll(discordGuildId, region)

        class MyEmbedFieldPageSource(menus.ListPageSource):
            def __init__(self, data):
                super().__init__(data, per_page=15)

            async def format_page(self, menu, entries):
                embed = nextcord.Embed(title="Registered list")
                for entry in entries:
                    embed.add_field(name=entry[0], value=entry[1], inline=False)
                embed.set_footer(
                    text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
                )
                return embed

        async def slash_pages(interaction: nextcord.Interaction):
            fields = []
            for user_obj in resutl_register_list:
                fields.append(
                    (
                        user_obj.albionNick,
                        f"Registered by: {user_obj.registerUserNick} - <@{user_obj.registerUserId}>\nLinked to: <@{user_obj.discordUserId}>",
                    )
                )
            pages = menus.ButtonMenuPages(
                source=MyEmbedFieldPageSource(fields),
                clear_buttons_after=True,
            )

            await pages.start(interaction=interaction)

        await slash_pages(interaction=interaction)

    @register.subcommand(description="Remove all registered users from the bot")
    @application_checks.check(checkRoleAdmin)
    async def clear(
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
        This is another subcommand of the '/register' slash command.
        It will appear in the menu as '/register show'.
        """

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.response.send_message(
                embed=embed_settings_error,
            )
            return

        embed_register_registered = nextcord.Embed(
            title="Confirm deletion of all registered users",
            description="This will not remove role from the users, just the data saved",
        )

        view = Confirm()

        await interaction.response.send_message(
            embed=embed_register_registered, view=view
        )

        view.message = await interaction.original_message()

        # Wait user confirmation
        await view.wait()

        if view.value:
            await registerDeleteAll(discordGuildId, region)
        else:
            return

    @register.subcommand(description="manual subcommand group")
    async def manual(self, interaction: Interaction):
        """
        This is a subcommand group of the '/register' slash command.
        All subcommands of this group will be prefixed with '/register force'.
        This will never get called since it has subcommands.
        """
        pass

    @manual.subcommand(
        description="Manually register an Albion Online nickname to a Discord user"
    )
    @application_checks.check(checkRole)
    async def addition(
        self,
        interaction: Interaction,
        discord_user: nextcord.Member = SlashOption(
            required=True,
            name="discord_user",
            description="Discord user to register",
        ),
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albion_nick: str = SlashOption(
            required=True,
            name="albion_nick",
            description="Albion Online user to register",
        ),
        albion_user_id: str = SlashOption(
            required=True,
            name="albion_user_id",
            description="Albion Online user ID",
        ),
        guild_tag: str = SlashOption(
            required=True,
            name="guild_tag",
            description="Guild tag",
        ),
        guild_tag_show: bool = SlashOption(
            required=True,
            name="show_guild_tag",
            description="Guild tag, used if public",
        ),
        alliance_tag: str = SlashOption(
            required=True,
            name="alliance_tag",
            description="Alliance tag",
        ),
        alliance_tag_show: bool = SlashOption(
            required=True,
            name="show_alliance_tag",
            description="Show alliance tag",
        ),
        role_1: nextcord.role.Role = SlashOption(
            required=True,
            name="role_to_give",
            description="Role to give to the user",
        ),
        role_2: nextcord.role.Role = SlashOption(
            required=False,
            name="another_role_to_give",
            description="Another role to give to the user",
            default=None,
        ),
    ):
        """
        This is a subcommand of the '/register manual' subcommand group.
        It will appear in the menu as '/register manual addition'.
        """

        await interaction.response.defer()

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.followup.send(
                embed=embed_settings_error,
            )
            return

        albion_nick_lower = albion_nick.lower()

        # Check if Albion Nick it's registered
        register_check_nick = await registerSelect(
            discordGuildId, albion_nick_lower, region
        )
        if register_check_nick is not None:
            embed_register_registered = nextcord.Embed(
                title="This Albion Online nicks it's already registered"
            )
            embed_register_registered.add_field(
                name="Albion Online nick:",
                value=f"{register_check_nick.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Used by:",
                value=f"<@{register_check_nick.discordUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registered by:",
                value=f"{register_check_nick.registerUserNick} - <@{register_check_nick.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="**Info:**",
                value="You can unregister this account with: /register manual deletion",
            )
            await interaction.followup.send(
                embed=embed_register_registered,
            )
            return

        # Check if Discord user ID it's registered
        register_check_discord = await registerSelectDiscord(
            discordGuildId, discord_user.id, region
        )
        if register_check_discord is not None:
            embed_register_registered = nextcord.Embed(
                title="This discord account it's already registered"
            )
            embed_register_registered.add_field(
                name="Albion Online nick:",
                value=f"{register_check_discord.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Used by:",
                value=f"<@{register_check_discord.discordUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registered by:",
                value=f"{register_check_discord.registerUserNick} - <@{register_check_discord.registerUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="**Info:**",
                value="You can unregister this account with: /register manual deletion",
            )
            await interaction.followup.send(
                embed=embed_register_registered,
            )
            return

        # Ask API
        apiResult = await albionApi("player", albion_user_id, region)

        # Check result
        checkApiResult = await check_api_result(apiResult["Found"])

        if checkApiResult is not False:
            await interaction.followup.send(
                embed=checkApiResult,
            )
            return

        # Process data
        albion_api_id_search = await apiPlayerInfoProcess(apiResult)

        # Check processed data
        checkProcessedResult = await check_api_result(albion_api_id_search["Found"])

        # Check processed data
        if checkProcessedResult is not False:
            await interaction.followup.send(
                embed=checkProcessedResult,
            )
            return

        try:
            if albion_api_id_search is not False:
                if albion_api_id_search["Name"] != albion_nick:
                    embed_id_not_found = nextcord.Embed(
                        title="Username mismatch error:"
                    )
                    embed_id_not_found.add_field(
                        name="Given username:", value=albion_nick, inline=False
                    )
                    embed_id_not_found.add_field(
                        name="Expected username:",
                        value=albion_api_id_search["Name"],
                        inline=False,
                    )
                    embed_id_not_found.add_field(
                        name="Info:",
                        value="Check if the user ID or username it's correct",
                        inline=False,
                    )
                    await interaction.followup.send(
                        embed=embed_id_not_found,
                    )
                    return
        except Exception as e:
            embed_id_not_found = nextcord.Embed(
                title="Error ocurred, log have been sent to the bot owner"
            )
            await interaction.followup.send(
                embed=embed_id_not_found,
            )
            logging.info(f"ERROR - {e} with {albion_nick} at /register manual addition")
            return

        nickTagOrder = settings.nickTagOrder

        # Enable/disable tags depending of settings
        if not guild_tag_show:
            guild_tag = ""
        else:
            guild_tag = "[" + guild_tag + "]"

        if not alliance_tag_show:
            alliance_tag = ""
        else:
            alliance_tag = "[" + alliance_tag + "]"

        # Show guild tag (yes/no) and alliance tag (yes/no)
        if nickTagOrder == 1:
            new_nick_value = (
                f"{alliance_tag} {guild_tag} {albion_api_id_search['Name']}"
            )
        elif nickTagOrder == 2:
            new_nick_value = (
                f"{guild_tag} {alliance_tag} {albion_api_id_search['Name']}"
            )

        roles_id = []

        roles_id.append(role_1.id)
        if role_2 is not None:
            roles_id.append(role_2.id)

        embed_register_add = nextcord.Embed(title="Registration info:")
        embed_register_add.add_field(
            name="Albion Online nickname:",
            value=f"{albion_api_id_search['Name']}",
            inline=False,
        )
        embed_register_add.add_field(
            name="Albion Online ID:",
            value=f"{albion_api_id_search['Id']}",
            inline=False,
        )
        if albion_api_id_search["GuildName"] != "":
            embed_register_add.add_field(
                name="Guild:",
                value=f"{albion_api_id_search['GuildName']}",
                inline=False,
            )
        if albion_api_id_search["GuildId"] != "":
            embed_register_add.add_field(
                name="Guild ID:",
                value=f"{albion_api_id_search['GuildId']}",
                inline=False,
            )
        if albion_api_id_search["AllianceName"] != "":
            embed_register_add.add_field(
                name="Alliance:",
                value=f"{albion_api_id_search['AllianceName']}",
                inline=False,
            )
        if albion_api_id_search["AllianceId"] != "":
            embed_register_add.add_field(
                name="Alliance ID:",
                value=f"{albion_api_id_search['AllianceId']}",
                inline=False,
            )
        for role_id in roles_id:
            embed_register_add.add_field(
                name="Rol added:", value=f"<@&{role_id}>", inline=False
            )
        embed_register_add.add_field(
            name="New nick:", value=new_nick_value, inline=False
        )
        embed_register_add.add_field(
            name=donations_name, value=donations_value, inline=False
        )

        view = Confirm()

        await interaction.followup.send(
            embed=embed_register_add,
            view=view,
        )

        view.message = await interaction.original_message()

        # Wait user confirmation
        await view.wait()

        if view.value:
            registered_with_error = False
            # Add roles
            for role_id in roles_id:
                try:
                    role = interaction.guild.get_role(int(role_id))

                except Exception as e:
                    logging.info(e)
                    embed_register_add.add_field(
                        name="Failed to add role:",
                        value=f"Role <@{role_id}> not found, make sure the role exist",
                        inline=False,
                    )
                    registered_with_error = True
                    pass
                try:
                    await discord_user.add_roles(role)
                except nextcord.errors.Forbidden:
                    embed_register_add.add_field(
                        name="Failed to add role:",
                        value="Missing permissions, **Manage role**, if you are an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be assigned, make sure it is above the roles you want to assign",
                        inline=False,
                    )
                    registered_with_error = True
                    pass
                except nextcord.errors.NotFound:
                    embed_register_add.add_field(
                        name="Failed to add role:",
                        value="Role not found, check if the role exist",
                        inline=False,
                    )
                    registered_with_error = True
                    pass
            # Change nick
            try:
                if settings.editNick == 1:
                    new_nick_value = new_nick_value[0:32]
                    await interaction.user.edit(nick=new_nick_value)
            except nextcord.errors.Forbidden:
                embed_register_add.add_field(
                    name="Failed to change nickname:",
                    value="Missing permissions, **Manage Nicknames**, if you are an admin it may be that the bot does not have permission to edit nicknames to admins, but to basic users.",
                    inline=False,
                )
                registered_with_error = True
                pass

            # Add user to DB
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

            if albion_api_id_search["GuildName"] == "":
                guild_name = "Info: Manual register"
            else:
                guild_name = albion_api_id_search["GuildName"]

            if albion_api_id_search["AllianceName"] == "":
                alliance_name = "Info: Manual register"
            else:
                alliance_name = albion_api_id_search["AllianceName"]

            try:
                await registerInsert(
                    discordGuildId,
                    discord_user.id,
                    albion_api_id_search["Id"],
                    albion_api_id_search["Name"],
                    interaction.user.id,
                    interaction.user.name,
                    dt_string,
                    guild_name,
                    alliance_name,
                    region,
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
                pass

            if registered_with_error:
                await interaction.edit_original_message(embed=embed_register_add)
            return
        else:
            return

    @manual.subcommand(
        description="Manually remove a registered user from a Discord user"
    )
    @application_checks.check(checkRole)
    async def deletion(
        self,
        interaction: Interaction,
        region: str = SlashOption(
            required=True,
            name="albion_region",
            description="Albion Online server region",
            choices=ao_regions,
        ),
        albionNick: str = SlashOption(
            required=True,
            name="albion_nick",
            description="Albion Online ingame nickname",
        ),
    ):
        """
        This is another subcommand of the '/register manual' subcommand group.
        It will appear in the menu as '/register manual remove'.
        """

        discordGuildId = interaction.guild_id

        # Check if bot it's configured
        settings = await settingsSelect(discordGuildId)
        if settings is None:
            embed_settings_error = nextcord.Embed(
                title="Error",
                description="The bot isn't configured, use /setup to configure the bot.\n\n If you think this it's an error contact with [Support Server](https://discord.gg/wxaqGTZWXS)",
            )
            await interaction.response.send_message(
                embed=embed_settings_error,
            )
            return

        albionNick_lower = albionNick.lower()

        # Check if Albion Online nick it's already registered
        register_check_nick = await registerSelect(
            discordGuildId, albionNick_lower, region
        )
        if register_check_nick is not None:
            embed_register_registered = nextcord.Embed(title="Confirm deletion:")
            embed_register_registered.add_field(
                name="Albion Online nick:",
                value=f"{register_check_nick.albionNick}",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Used by:",
                value=f"<@{register_check_nick.discordUserId}>",
                inline=False,
            )
            embed_register_registered.add_field(
                name="Registered by:",
                value=f"{register_check_nick.registerUserNick} - <@{register_check_nick.registerUserId}>",
                inline=False,
            )

            view = Confirm()

            await interaction.response.send_message(
                embed=embed_register_registered, view=view
            )
            view.message = await interaction.original_message()
        else:
            embed_register_not_registered = nextcord.Embed(
                title="Error",
                description=f"{albionNick} Albion Online nick isn't registered",
            )
            await interaction.response.send_message(
                embed=embed_register_not_registered,
            )
            return

        # Wait user confirmation
        await view.wait()

        if view.value:
            # Remove registration
            await registerDeleteAlbionNick(discordGuildId, albionNick, region)

            edit_errors = False
            embed_edit_errors = nextcord.Embed(title="Error")

            # Get member info
            try:
                discordId = register_check_nick.discordUserId
                member = await interaction.guild.fetch_member(discordId)
            except nextcord.errors.NotFound:
                return

            # Remove roles
            try:
                await member.edit(roles=[])
            except nextcord.errors.Forbidden:
                embed_edit_errors.add_field(
                    name="Missing permissions:",
                    value="**Manage roles**, if you are an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be assigned, make sure it is above the roles you want to assign",
                    inline=False,
                )
                edit_errors = True
                pass
            except nextcord.errors.NotFound:
                pass

            # Remove nick
            try:
                await member.edit(nick=None)
            except nextcord.errors.Forbidden:
                embed_edit_errors.add_field(
                    name="Missing permissions:",
                    value="**Manage nicknames**, if you are an admin it may be that the bot does not have permissions to assign roles or that the bot role is below the roles to be assigned, make sure it is above the roles you want to assign",
                    inline=False,
                )
                edit_errors = True
                pass
            except nextcord.errors.NotFound:
                pass

            if edit_errors:
                await interaction.edit_original_message(embed=embed_edit_errors)
            return
        else:
            return


def setup(bot):
    bot.add_cog(register(bot))
