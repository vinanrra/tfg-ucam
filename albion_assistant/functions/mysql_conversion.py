"""
    Convert numbers from MySQL data to String
"""

async def nickAllyTagToString(nickAllyTag):
    if nickAllyTag == 1:
        nick_ally_tag_string = "Only to alliance members"
    elif nickAllyTag == 2:
        nick_ally_tag_string = "Only to guild members"
    elif nickAllyTag == 3:
        nick_ally_tag_string = "Everyone"
    else:
        nick_ally_tag_string = "Don't show"
    return nick_ally_tag_string


async def nickGuildTagToString(nickGuildTag):
    if nickGuildTag == 1:
        nick_guild_tag_string = "Only to alliance members"
    elif nickGuildTag == 2:
        nick_guild_tag_string = "Only to guild members"
    elif nickGuildTag == 3:
        nick_guild_tag_string = "Everyone"
    else:
        nick_guild_tag_string = "Don't show"
    return nick_guild_tag_string


async def nickTagOrderToString(nickTagOrder):
    if nickTagOrder == 1:
        nick_tag_order = "[ALLY] [GUILD]"
    else:
        nick_tag_order = "[GUILD] [ALLY]"
    return nick_tag_order


async def publicToString(public):
    if public == 1:
        public_string = "Yes"
    else:
        public_string = "No"
    return public_string


async def globalBlacklistWarningToString(globalBlacklistWarning):
    if globalBlacklistWarning == 1:
        global_blacklist_warning = "Yes"
    else:
        global_blacklist_warning = "No"
    return global_blacklist_warning


async def publicBlacklistToString(publicBlacklist):
    if publicBlacklist == 1:
        public_blacklist = "Yes"
    else:
        public_blacklist = "No"
    return public_blacklist


async def purgeUsersToString(purgeUsers):
    if purgeUsers == 1:
        purge_users = "Yes"
    else:
        purge_users = "No"
    return purge_users


async def editNickToString(editNick):
    if editNick == 1:
        edit_nick = "Yes"
    else:
        edit_nick = "No"
    return edit_nick


async def blacklistTypeToString(blacklistType: int):
    if blacklistType == 1:
        blacklistTypeString = "User"
    elif blacklistType == 2:
        blacklistTypeString = "Guild"
    elif blacklistType == 3:
        blacklistTypeString = "Alliance"
    return blacklistTypeString
