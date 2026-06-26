from nextcord import Interaction

from functions.mysql import settingsSelect


async def checkOwner(interaction: Interaction):
    """Check whether the user who triggered the interaction is the owner of the guild or has administrative privileges.

    Args:
        interaction (Interaction): The interaction object representing the command being executed.

    Returns:
        bool: True if the user is the guild owner or has administrative privileges, False otherwise.
    """

    if interaction.guild.owner_id == interaction.user.id:
        return True

    if interaction.user.guild_permissions.administrator:
        return True

    return False


async def checkRole(interaction: Interaction):
    """
    Check if the user has permission to execute the command based on their role.

    Args:
        interaction (Interaction): The interaction object representing the command being executed.

    Returns:
        bool: True if the user has permission, False otherwise.
    """

    if interaction.guild.owner_id == interaction.user.id:
        return True

    elif interaction.user.guild_permissions.administrator:
        return True

    else:
        discordGuildId = interaction.guild_id
        settings = await settingsSelect(discordGuildId)

        try:
            roleAdmin: int = int(settings.adminRole)
            roleMod: int = int(settings.modRole)
        except:
            return False

        for Role in interaction.user.roles:
            if Role.id == roleAdmin:
                return True
            elif Role.id == roleMod:
                return True

    return False


async def checkRoleAdmin(interaction: Interaction):
    """
    Check if the user has the admin role for the server.

    Args:
        interaction (Interaction): The interaction object representing the command being executed.

    Returns:
        bool: True if the user has the admin role, False otherwise.
    """

    if interaction.guild.owner_id == interaction.user.id:
        return True
    elif interaction.user.guild_permissions.administrator:
        return True
    else:
        discordGuildId = interaction.guild_id
        settings = await settingsSelect(discordGuildId)

        try:
            roleAdmin: int = int(settings.adminRole)
        except:
            return False

        for Role in interaction.user.roles:
            if Role.id == roleAdmin:
                return True

    return False


async def checkRoleMod(interaction: Interaction):
    """
    Checks if the user has the required mod role or higher to use a command.

    Args:
        interaction (Interaction): The interaction object representing the command being executed.

    Returns:
        bool: True if the user has the required role or higher, False otherwise.
    """

    if interaction.guild.owner_id == interaction.user.id:
        return True
    elif interaction.user.guild_permissions.administrator:
        return True
    else:
        discordGuildId = interaction.guild_id
        settings = await settingsSelect(discordGuildId)

        try:
            roleMod: int = int(settings.modRole)
        except:
            return False

        for Role in interaction.user.roles:
            if Role.id == roleMod:
                return True

    return False


# async def checkRoleBankManager(interaction: Interaction):

#     if interaction.guild.owner_id == interaction.user.id:
#       return True
#     elif interaction.user.guild_permissions.administrator:
#       return True
#     else:

#       discordGuildId = interaction.guild_id
#       bankSettings = await bankSettingsSelect(discordGuildId)

#       try:
#         roleBankManager : int = int(bankSettings.managerRole)
#       except:
#         return False

#       for Role in interaction.user.roles:
#         if Role.id == roleBankManager:
#           return True

#     return False
