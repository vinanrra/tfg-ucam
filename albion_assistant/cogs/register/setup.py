import nextcord
from functions.embebs import Confirm, donations_name, donations_value
from functions.mysql import settingsDelete, settingsInsert, settingsSelect
from functions.mysql_conversion import (
    editNickToString,
    globalBlacklistWarningToString,
    nickAllyTagToString,
    nickGuildTagToString,
    nickTagOrderToString,
    publicBlacklistToString,
    publicToString,
    purgeUsersToString,
)
from functions.perms import checkRoleAdmin
from nextcord import Interaction, SlashOption
from nextcord.ext import application_checks, commands

TESTING_GUILD_ID = 419816336768630794  # Replace with your testing guild id


class setupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(description="setup command")
    async def setup(self, interaction: Interaction):
        """
        This is the setup slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass

    @setup.subcommand(description="Show bot settings")
    @application_checks.check(checkRoleAdmin)
    # Show  bot settings
    async def show(self, interaction: Interaction):
        """
        This is a subcommand of the '/setup' slash command.
        It will appear in the menu as '/setup show'.
        """

        discordGuildId = interaction.guild_id

        settings = await settingsSelect(discordGuildId)

        if settings != None:
            public = settings.public
            public_role = settings.publicRole
            adminRole = settings.adminRole
            modRole = settings.modRole
            globalBlacklistWarning = settings.globalBlacklistWarning
            publicBlacklist = settings.publicBlacklist
            purgeUsers = settings.purgeUsers
            editNick = settings.editNick
            nickAllyTag = settings.nickAllyTag
            nickAllyTagLenght = settings.nickAllyTagLenght
            nickGuildTag = settings.nickGuildTag
            nickGuildTagLenght = settings.nickGuildTagLenght
            nickTagOrder = settings.nickTagOrder

            # Numbers to string
            nick_ally_tag_string = await nickAllyTagToString(nickAllyTag)
            nick_guild_tag_string = await nickGuildTagToString(nickGuildTag)
            nick_tag_order = await nickTagOrderToString(nickTagOrder)
            public_string = await publicToString(public)
            global_blacklist_warning = await globalBlacklistWarningToString(
                globalBlacklistWarning
            )
            public_blacklist = await publicBlacklistToString(publicBlacklist)
            purge_users = await purgeUsersToString(purgeUsers)
            edit_nick = await editNickToString(editNick)

            embed_settings = nextcord.Embed(title="Settings")
            embed_settings.add_field(
                name="Public server:", value=f"{public_string}", inline=False
            )
            if public == 1:
                embed_settings.add_field(
                    name="Public role:", value=f"{public_role}", inline=False
                )
            embed_settings.add_field(
                name="Admin role:", value=f"<@&{adminRole}>", inline=False
            )
            embed_settings.add_field(
                name="Mod role:", value=f"<@&{modRole}>", inline=False
            )
            embed_settings.add_field(
                name="Blacklist global warning:",
                value=f"{global_blacklist_warning}",
                inline=False,
            )
            embed_settings.add_field(
                name="Public blacklist:", value=f"{public_blacklist}", inline=False
            )
            embed_settings.add_field(
                name="On leave remove user roles:", value=f"{purge_users}", inline=False
            )
            embed_settings.add_field(
                name="Edit nick:", value=f"{edit_nick}", inline=False
            )
            embed_settings.add_field(
                name="Add alliance tag before name:",
                value=f"{nick_ally_tag_string}",
                inline=False,
            )
            embed_settings.add_field(
                name="Alliance tag lenght:", value=f"{nickAllyTagLenght}", inline=False
            )
            embed_settings.add_field(
                name="Add guild tag before name:",
                value=f"{nick_guild_tag_string}",
                inline=False,
            )
            embed_settings.add_field(
                name="Guild tag lenght:", value=f"{nickGuildTagLenght}", inline=False
            )
            embed_settings.add_field(
                name="Tags order", value=f"{nick_tag_order}", inline=False
            )
            embed_settings.add_field(
                name=donations_name, value=donations_value, inline=False
            )
        else:
            embed_settings = nextcord.Embed(
                title="No settings found",
                description="Configure the bot with **/setup config**",
            )
            embed_settings.add_field(
                name=donations_name, value=donations_value, inline=False
            )

        await interaction.response.send_message(embed=embed_settings)

    @setup.subcommand(description="Configure the bot settings")
    @application_checks.check(checkRoleAdmin)
    # Configure the bot
    async def config(
        self,
        interaction: Interaction,
        public: int = SlashOption(
            required=True,
            name="public",
            description="Allow everyone to register, even if they aren't at your guild or alliance",
            choices={
                "Yes": 1,
                "No": 2,
            },
        ),
        public_role: nextcord.role.Role = SlashOption(
            required=True,
            name="public_role",
            description="Role to add to users if server it's public",
        ),
        adminRole: nextcord.role.Role = SlashOption(
            required=True,
            name="admin_role",
            description="Role that will be able to fully configure the bot",
        ),
        modRole: nextcord.role.Role = SlashOption(
            required=True,
            name="mod_role",
            description="Role that will be able to manage users and see bot configuration",
        ),
        globalBlacklistWarning: int = SlashOption(
            required=True,
            name="global_blacklist_warning",
            description="WIP - Do you want to show a warning if the user have been blacklisted in another server?",
            choices={
                "Yes": 1,
                "No": 2,
            },
            default=2,
        ),
        publicBlacklist: int = SlashOption(
            required=True,
            name="public_blacklist",
            description="Allow other servers to view your blacklist, used for warnings at registration",
            choices={
                "Yes": 1,
                "No": 2,
            },
            default=2,
        ),
        purgeUsers: int = SlashOption(
            required=True,
            name="purge_users_on_leave",
            description="WIP - If enable when an user leave any configured guild/alliance the bot will remove the added roles",
            choices={
                "Yes": 1,
                "No": 2,
            },
            default=2,
        ),
        editNick: int = SlashOption(
            required=True,
            name="edit_nick",
            description="The bot will change user nickname to Albion Online nickname when registered",
            choices={
                "Yes": 1,
                "No": 2,
            },
            default=1,
        ),
        nickAllyTag: int = SlashOption(
            required=True,
            name="nick_ally_tag",
            description="Add alliance tag before name",
            choices={
                "Only to alliance members": 1,
                "Only to guild members": 2,
                "Everyone": 3,
                "Don't show": 4,
            },
            default=3,
        ),
        nickAllyTagLenght: int = SlashOption(
            required=True,
            name="nick_ally_tag_lenght",
            description="Alliance tag lenght",
            choices={"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7},
            default=5,
        ),
        nickGuildTag: int = SlashOption(
            required=True,
            name="nick_guild_tag",
            description="Add guild tag before name",
            choices={
                "Only to alliance members": 1,
                "Only to guild members": 2,
                "Everyone": 3,
                "Don't show": 4,
            },
            default=3,
        ),
        nickGuildTagLenght: int = SlashOption(
            required=True,
            name="nick_guild_tag_lenght",
            description="Guild tag lenght",
            choices={"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7},
            default=5,
        ),
        nickTagOrder: int = SlashOption(
            required=True,
            name="nick_tag_order",
            description="Tag to show first in the name",
            choices={
                "Alliance": 1,
                "Guild": 2,
            },
            default=1,
        ),
    ):
        """
        This is a subcommand of the '/setup' slash command.
        It will appear in the menu as '/setup config'.
        """

        # Numbers to string
        nick_ally_tag_string = await nickAllyTagToString(nickAllyTag)
        nick_guild_tag_string = await nickGuildTagToString(nickGuildTag)
        nick_tag_order = await nickTagOrderToString(nickTagOrder)
        public_string = await publicToString(public)
        global_blacklist_warning = await globalBlacklistWarningToString(
            globalBlacklistWarning
        )
        public_blacklist = await publicBlacklistToString(publicBlacklist)
        purge_users = await purgeUsersToString(purgeUsers)
        edit_nick = await editNickToString(editNick)

        embed_settings = nextcord.Embed(title="Settings:")
        embed_settings.add_field(
            name="Public server:", value=f"{public_string}", inline=False
        )
        if public != 1:
            embed_settings.add_field(
                name="Public role:", value=f"<@&{public_role.id}>", inline=False
            )
        embed_settings.add_field(
            name="Admin role:", value=f"<@&{adminRole.id}>", inline=False
        )
        embed_settings.add_field(
            name="Mod role:", value=f"<@&{modRole.id}>", inline=False
        )
        embed_settings.add_field(
            name="Blacklist global warning:",
            value=f"{global_blacklist_warning}",
            inline=False,
        )
        embed_settings.add_field(
            name="Public blacklist:", value=f"{public_blacklist}", inline=False
        )
        embed_settings.add_field(
            name="On leave remove user roles:", value=f"{purge_users}", inline=False
        )
        embed_settings.add_field(name="Edit nick:", value=f"{edit_nick}", inline=False)
        embed_settings.add_field(
            name="Add alliance tag before name:",
            value=f"{nick_ally_tag_string}",
            inline=False,
        )
        embed_settings.add_field(
            name="Alliance tag lenght:", value=f"{nickAllyTagLenght}", inline=False
        )
        embed_settings.add_field(
            name="Add guild tag before name:",
            value=f"{nick_guild_tag_string}",
            inline=False,
        )
        embed_settings.add_field(
            name="Guild tag lenght:", value=f"{nickGuildTagLenght}", inline=False
        )
        embed_settings.add_field(
            name="Tags order", value=f"{nick_tag_order}", inline=False
        )
        embed_settings.add_field(
            name=donations_name, value=donations_value, inline=False
        )

        view = Confirm()

        await interaction.response.send_message(embed=embed_settings, view=view)

        view.message = await interaction.original_message()
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            discordGuildId = interaction.guild_id

            await settingsInsert(
                discordGuildId,
                public,
                public_role.id,
                adminRole.id,
                modRole.id,
                editNick,
                nickAllyTag,
                nickAllyTagLenght,
                nickGuildTag,
                nickGuildTagLenght,
                nickTagOrder,
                globalBlacklistWarning,
                purgeUsers,
                publicBlacklist,
            )
            return
        else:
            return

    @setup.subcommand(description="Delete bot all settings and data")
    @application_checks.check(checkRoleAdmin)
    # Remove  bot settings
    async def delete(self, interaction: Interaction):
        """
        This is a subcommand of the '/setup' slash command.
        It will appear in the menu as '/setup delete'.
        """

        discordGuildId = interaction.guild_id
        settings = await settingsSelect(discordGuildId)

        if settings is None:
            embed_settings_not_configured = nextcord.Embed(
                title="No settings found",
                description="Configure the bot with **/setup config**",
            )
            embed_settings_not_configured.add_field(
                name=donations_name, value=donations_value, inline=False
            )

            await interaction.response.send_message(embed=embed_settings_not_configured)
            return

        embed_delete = nextcord.Embed(
            title="Do you want to delete the bot settings and data?"
        )
        embed_delete.add_field(name=donations_name, value=donations_value, inline=False)

        view = Confirm()

        await interaction.response.send_message(
            embed=embed_delete,
            view=view,
        )

        view.message = await interaction.original_message()

        await view.wait()

        if view.value is None:
            return
        elif view.value:
            await settingsDelete(discordGuildId)
            return
        else:
            return


def setup(bot):
    bot.add_cog(setupCog(bot))
