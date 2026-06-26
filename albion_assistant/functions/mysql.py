import sqlalchemy
import sqlalchemy.exc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import ForeignKey, Integer, VARCHAR, Column, UniqueConstraint, insert
from sqlalchemy import select, update, delete
import os

# Connection
mysql_user = os.environ["mysqlUser"]
mysql_pass = os.environ["mysqlPass"]
mysql_host = os.environ["mysqlHost"]
mysql_port = os.environ["mysqlPort"]
mysql_db = os.environ["mysqldb"]

# Register table names
mysql_table_config = os.environ["mysqlTableConfig"]
mysql_table_guild = os.environ["mysqlTableGuild"]
mysql_table_alliance = os.environ["mysqlTableAlliance"]
mysql_table_user = os.environ["mysqlTableRegister"]
mysql_table_blacklist = os.environ["mysqlTableBlacklist"]
mysql_table_region = os.environ["mysqlTableRegion"]

Base = declarative_base()

engine = create_async_engine(
    f"mysql+asyncmy://{mysql_user}:{mysql_pass}@{mysql_host}:{mysql_port}/{mysql_db}"
)

###################
# REGISTER TABLES #
###################


class TableRegion(Base):
    """
    Represents a region in the MySQL database table `mysql_table_region`.

    Attributes:
        idRegion (int): The primary key for the region.
        serverRegion (str): The name of the server region, stored as a string.

    Table metadata:
        __tablename__ (str): The name of the MySQL table.
        __table_args__ (tuple): Additional table arguments, including a unique constraint on `serverRegion`.
    """

    __tablename__ = mysql_table_region
    __table_args__ = (UniqueConstraint("serverRegion"), {"extend_existing": True})

    idRegion = Column(Integer, primary_key=True, autoincrement=True)
    serverRegion = Column(VARCHAR(19), nullable=False, unique=True)


async def region_insert(region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            check = select(TableRegion).filter_by(serverRegion=region)
            check_query = await session.execute(check)
            check_result = check_query.scalars().first()
            try:
                if check_result is None:
                    session.add_all(
                        [
                            TableRegion(
                                serverRegion=region,
                            ),
                        ]
                    )
                    await session.commit()
            finally:
                await session.close()


async def region_select():
    """
    Asynchronously queries all `serverRegion` values from the `TableRegion` table
    and returns them as a list of strings.

    Returns:
        A list of strings representing the `serverRegion` values.

    Raises:
        Any exception raised by the database engine or session during the query.

    Usage:
        regions = await regionSelect()
    """
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            server_regions = await session.execute(select(TableRegion))
            await session.close()

        return server_regions.scalars()


class tableSetting(Base):
    __tablename__ = mysql_table_config
    __table_args__ = {"extend_existing": True}

    discordGuildId = Column(VARCHAR(19), primary_key=True, autoincrement=False)
    public = Column(Integer)
    publicRole = Column(VARCHAR(19))
    adminRole = Column(VARCHAR(19))
    modRole = Column(VARCHAR(19))
    editNick = Column(Integer)
    nickAllyTag = Column(Integer)
    nickAllyTagLenght = Column(Integer)  # Max 7
    nickGuildTag = Column(Integer)
    nickGuildTagLenght = Column(Integer)  # Max 7
    nickTagOrder = Column(Integer)
    globalBlacklistWarning = Column(Integer)
    purgeUsers = Column(Integer)
    publicBlacklist = Column(Integer)


async def settingsInsert(
    discordGuildId_data: int,
    public_data: int,
    publicRole_data: str,
    adminRole_data: int,
    modRole_data: int,
    editNick_data: int,
    nickAllyTag_data: int,
    nickAllyTagLenght_data: int,
    nickGuildTag_data: int,
    nickGuildTagLenght_data: int,
    nickTagOrder_data: int,
    globalBlacklistWarning_data: int,
    purgeUsers_data: int,
    publicBlacklist: int,
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            check_guild = select(tableSetting).filter_by(
                discordGuildId=discordGuildId_data
            )
            check_guild_query = await session.execute(check_guild)
            check_guild_result = check_guild_query.scalars().first()

            try:
                if check_guild_result == None:
                    session.add_all(
                        [
                            tableSetting(
                                discordGuildId=discordGuildId_data,
                                public=public_data,
                                publicRole=publicRole_data,
                                adminRole=adminRole_data,
                                modRole=modRole_data,
                                editNick=editNick_data,
                                nickAllyTag=nickAllyTag_data,
                                nickAllyTagLenght=nickAllyTagLenght_data,
                                nickGuildTag=nickGuildTag_data,
                                nickGuildTagLenght=nickGuildTagLenght_data,
                                nickTagOrder=nickTagOrder_data,
                                globalBlacklistWarning=globalBlacklistWarning_data,
                                purgeUsers=purgeUsers_data,
                                publicBlacklist=publicBlacklist,
                            ),
                        ]
                    )
                    await session.commit()
                else:
                    settings_update = (
                        update(tableSetting)
                        .where(tableSetting.discordGuildId == discordGuildId_data)
                        .values(
                            public=public_data,
                            publicRole=publicRole_data,
                            adminRole=adminRole_data,
                            modRole=modRole_data,
                            editNick=editNick_data,
                            nickAllyTag=nickAllyTag_data,
                            nickAllyTagLenght=nickAllyTagLenght_data,
                            nickGuildTag=nickGuildTag_data,
                            nickGuildTagLenght=nickGuildTagLenght_data,
                            nickTagOrder=nickTagOrder_data,
                            globalBlacklistWarning=globalBlacklistWarning_data,
                            purgeUsers=purgeUsers_data,
                            publicBlacklist=publicBlacklist,
                        )
                    )
                    await session.execute(settings_update)
                    await session.commit()
            finally:
                await session.close()


async def settingsSelect(discordGuildId_data: int):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            settings_select = select(tableSetting).where(
                tableSetting.discordGuildId == discordGuildId_data
            )
            try:
                result = await session.execute(settings_select)
            finally:
                await session.close()

        return result.scalar()


async def settingsDelete(discordGuildId_data: int):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            settings_delete = delete(tableSetting).where(
                tableSetting.discordGuildId == discordGuildId_data
            )

            try:
                await session.execute(settings_delete)
                await session.commit()

            finally:
                await session.close()


class tableGuild(Base):
    __tablename__ = mysql_table_guild
    __table_args__ = {"extend_existing": True}

    discordGuildId = Column(
        VARCHAR(19),
        ForeignKey(f"{mysql_table_config}.discordGuildId", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    albionGuildId = Column(VARCHAR(25), primary_key=True, autoincrement=False)
    albionGuildName = Column(VARCHAR(40))
    guildRole = Column(VARCHAR(19))
    guildTag = Column(VARCHAR(7))
    serverRegionFK = Column(
        VARCHAR(19), ForeignKey(f"{mysql_table_region}.serverRegion")
    )


async def guildInsert(
    discordGuildId_data: int,
    albionGuildId_data: str,
    albionGuildName_data: str,
    guildRole_data: int,
    guildTag_data: str,
    region: str,
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            check_guild_table = select(tableGuild).filter_by(
                discordGuildId=discordGuildId_data, albionGuildId=albionGuildId_data
            )
            check_guild_table_query = await session.execute(check_guild_table)
            check_guild__table_result = check_guild_table_query.scalars().first()

            try:
                if check_guild__table_result == None:
                    session.add_all(
                        [
                            tableGuild(
                                discordGuildId=discordGuildId_data,
                                albionGuildId=albionGuildId_data,
                                albionGuildName=albionGuildName_data,
                                guildRole=guildRole_data,
                                guildTag=guildTag_data,
                                serverRegionFK=region,
                            ),
                        ]
                    )
                    await session.commit()
                else:
                    guild_update = (
                        update(tableGuild)
                        .where(
                            tableGuild.discordGuildId == discordGuildId_data,
                            tableGuild.albionGuildId == albionGuildId_data,
                        )
                        .values(
                            guildRole=guildRole_data,
                            guildTag=guildTag_data,
                        )
                    )
                    await session.execute(guild_update)
                    await session.commit()
            finally:
                await session.close()


async def guildSelect(discordGuildId_data: int, albionGuildId_data: str, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            guild_select = select(tableGuild).where(
                tableGuild.discordGuildId == discordGuildId_data,
                tableGuild.albionGuildId == albionGuildId_data,
                tableGuild.serverRegionFK == region,
            )
            try:
                result = await session.execute(guild_select)
            finally:
                await session.close()

        return result.scalar()


async def guildSelectAll(discordGuildId_data: int, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                guild_select_all_result = await session.execute(
                    select(tableGuild)
                    .where(
                        tableGuild.discordGuildId == discordGuildId_data,
                        tableGuild.serverRegionFK == region,
                    )
                    .order_by(tableGuild.albionGuildName)
                )
            finally:
                await session.close()

        return guild_select_all_result.scalars()


async def guildSelectAllNames(discordGuildId_data: int, region: str):
    """
    A function that retrieves all guilds names from the database.

    Args:
        discordGuildId_data (int): Discord Guild ID

    Returns:
        list : A list of all guilds names in the database filtered by discord guild ID, ordered by name.
    """
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                guild_select_all_result = await session.execute(
                    select(tableGuild.albionGuildName)
                    .where(
                        tableGuild.discordGuildId == discordGuildId_data,
                        tableGuild.serverRegionFK == region,
                    )
                    .order_by(tableGuild.albionGuildName)
                )
            finally:
                await session.close()

        return guild_select_all_result.scalars()


async def guildDelete(discordGuildId_data: int, albionGuildId_data: str, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            guild_select = delete(tableGuild).where(
                tableGuild.discordGuildId == discordGuildId_data,
                tableGuild.albionGuildId == albionGuildId_data,
                tableGuild.serverRegionFK == region,
            )

            try:
                await session.execute(guild_select)
                await session.commit()

            finally:
                await session.close()


async def guildAll(region: str):
    """
    A function that retrieves all guilds from the database.

    Returns:
        scalar : A scalar of all guilds in the database, ordered by name.
    """

    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                guild_select_all_result = await session.execute(
                    select(tableGuild)
                    .where(
                        tableGuild.serverRegionFK == region,
                    )
                    .order_by(tableGuild.albionGuildName)
                )
            finally:
                await session.close()

        return guild_select_all_result.scalars().all()


async def guildSelectAllDiscordIdByGuildId(albionGuildId_data: str, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                guild_select_all_result = await session.execute(
                    select(tableGuild)
                    .where(
                        tableGuild.albionGuildId == albionGuildId_data,
                        tableGuild.serverRegionFK == region,
                    )
                    .order_by(tableGuild.albionGuildName)
                )
            finally:
                await session.close()

        return guild_select_all_result.scalars()


class tableAlliance(Base):
    __tablename__ = mysql_table_alliance
    __table_args__ = {"extend_existing": True}

    discordGuildId = Column(
        VARCHAR(19),
        ForeignKey(f"{mysql_table_config}.discordGuildId", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    albionAllianceId = Column(VARCHAR(25), primary_key=True, autoincrement=False)
    albionAllianceName = Column(VARCHAR(50))
    allianceRole = Column(VARCHAR(19))
    allianceTag = Column(VARCHAR(7))
    serverRegionFK = Column(
        VARCHAR(19), ForeignKey(f"{mysql_table_region}.serverRegion")
    )


async def allianceSelect(
    discordGuildId_data: int, albionAllianceId_data: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            alliance_select = select(tableAlliance).where(
                tableAlliance.discordGuildId == discordGuildId_data,
                tableAlliance.albionAllianceId == albionAllianceId_data,
                tableAlliance.serverRegionFK == region,
            )
            try:
                result = await session.execute(alliance_select)
            finally:
                await session.close()

        return result.scalar()


async def allianceInsert(
    discordGuildId_data: int,
    albionAllianceId_data: str,
    albionGuildName_data: str,
    AllianceRole_data: int,
    allianceTag_data: str,
    region: str,
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            check_alliance_table = select(tableAlliance).filter_by(
                discordGuildId=discordGuildId_data,
                albionAllianceId=albionAllianceId_data,
                serverRegionFK=region,
            )
            check_alliance_table_query = await session.execute(check_alliance_table)
            check_alliance_table_result = check_alliance_table_query.scalars().first()

            try:
                if check_alliance_table_result == None:
                    session.add_all(
                        [
                            tableAlliance(
                                discordGuildId=discordGuildId_data,
                                albionAllianceId=albionAllianceId_data,
                                albionAllianceName=albionGuildName_data,
                                allianceRole=AllianceRole_data,
                                allianceTag=allianceTag_data,
                                serverRegionFK=region,
                            ),
                        ]
                    )
                    await session.commit()
                else:
                    alliance_update = (
                        update(tableAlliance)
                        .where(
                            tableAlliance.discordGuildId == discordGuildId_data,
                            tableAlliance.albionAllianceId == albionAllianceId_data,
                            tableAlliance.serverRegionFK == region,
                        )
                        .values(
                            allianceRole=AllianceRole_data,
                            allianceTag=allianceTag_data,
                            serverRegionFK=region,
                        )
                    )
                    await session.execute(alliance_update)
                    await session.commit()
            finally:
                await session.close()


async def allianceDelete(
    discordGuildId_data: int, albionAllianceId_data: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            alliance_delete = delete(tableAlliance).where(
                tableAlliance.discordGuildId == discordGuildId_data,
                tableAlliance.albionAllianceId == albionAllianceId_data,
                tableAlliance.serverRegionFK == region,
            )

            try:
                await session.execute(alliance_delete)
                await session.commit()

            finally:
                await session.close()


async def allianceSelectAll(discordGuildId_data: int, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                alliance_select_all_result = await session.execute(
                    select(tableAlliance)
                    .where(
                        tableAlliance.discordGuildId == discordGuildId_data,
                        tableAlliance.serverRegionFK == region,
                    )
                    .order_by(tableAlliance.albionAllianceName)
                )
            finally:
                await session.close()

        return alliance_select_all_result.scalars()


class tableUser(Base):
    __tablename__ = mysql_table_user
    __table_args__ = {"extend_existing": True}

    discordGuildId = Column(
        VARCHAR(19),
        ForeignKey(f"{mysql_table_config}.discordGuildId", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    discordUserId = Column(VARCHAR(19))
    albionUserId = Column(VARCHAR(25), primary_key=True, autoincrement=False)
    albionNick = Column(VARCHAR(16))
    registerUserId = Column(
        VARCHAR(19)
    )  # Will be the Discord user ID who registered that nickname, usefull if forceregister
    registerUserNick = Column(
        VARCHAR(33)
    )  # Will be the user Discord nickname who registered that nickname, usefull if forceregister
    registerDate = Column(VARCHAR(19))
    registerGuild = Column(VARCHAR(30))
    registerAlliance = Column(VARCHAR(30))
    serverRegionFK = Column(
        VARCHAR(19), ForeignKey(f"{mysql_table_region}.serverRegion")
    )


async def registerSelect(discordGuildId_data: int, albionNick_data: str, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            register_select = select(tableUser).where(
                tableUser.discordGuildId == discordGuildId_data,
                tableUser.albionNick == albionNick_data,
                tableUser.serverRegionFK == region,
            )
            try:
                result = await session.execute(register_select)
            finally:
                await session.close()

        return result.scalar()


async def registerSelectDiscord(discordGuildId_data: int, discorUserdId: str, region):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            register_select_discord = select(tableUser).where(
                tableUser.discordGuildId == discordGuildId_data,
                tableUser.discordUserId == discorUserdId,
                tableUser.serverRegionFK == region,
            )
            try:
                result = await session.execute(register_select_discord)
            finally:
                await session.close()

        return result.scalar()


async def registerInsert(
    discordGuildId_data: int,
    discordUserId_data: str,
    albionUserId_data: str,
    albionNick_data: int,
    registerUserId_data: str,
    registerUserNick_data: str,
    date_date: str,
    guildName_data: str,
    allianceName_data: str,
    region_data: str,
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                query = insert(tableUser).values(
                    discordGuildId=discordGuildId_data,
                    discordUserId=discordUserId_data,
                    albionUserId=albionUserId_data,
                    albionNick=albionNick_data,
                    registerUserId=registerUserId_data,
                    registerUserNick=registerUserNick_data,
                    registerDate=date_date,
                    registerGuild=guildName_data,
                    registerAlliance=allianceName_data,
                    serverRegionFK=region_data,
                )
                await session.execute(query)
                await session.commit()
            except sqlalchemy.exc.IntegrityError:
                query = (
                    update(tableUser)
                    .where(
                        tableUser.discordGuildId == discordGuildId_data,
                        tableUser.discordUserId == discordUserId_data,
                        tableUser.serverRegionFK == region_data,
                    )
                    .values(
                        discordGuildId=discordGuildId_data,
                        discordUserId=discordUserId_data,
                        albionUserId=albionUserId_data,
                        albionNick=albionNick_data,
                        registerUserId=registerUserId_data,
                        registerUserNick=registerUserNick_data,
                        registerDate=date_date,
                        registerGuild=guildName_data,
                        registerAlliance=allianceName_data,
                        serverRegionFK=region_data,
                    )
                )
                await session.execute(query)
                await session.commit()
            finally:
                await session.close()


async def registerDeleteDiscord(
    discordGuildId_data: int, discorUserdId: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            discord_id_delete = delete(tableUser).where(
                tableUser.discordGuildId == discordGuildId_data,
                tableUser.discordUserId == discorUserdId,
                tableUser.serverRegionFK == region,
            )
            try:
                await session.execute(discord_id_delete)
                await session.commit()
            finally:
                await session.close()


async def registerDeleteAll(discordGuildId_data: int, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            discord_id_delete = delete(tableUser).where(
                tableUser.discordGuildId == discordGuildId_data,
                tableUser.serverRegionFK == region,
            )
            try:
                await session.execute(discord_id_delete)
                await session.commit()
            finally:
                await session.close()


async def registerDeleteAlbionNick(
    discordGuildId_data: int, albionNick_data: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            discord_albion_nick_delete = delete(tableUser).where(
                tableUser.discordGuildId == discordGuildId_data,
                tableUser.albionNick == albionNick_data,
                tableUser.serverRegionFK == region,
            )
            try:
                await session.execute(discord_albion_nick_delete)
                await session.commit()
            finally:
                await session.close()


async def registerSelectAll(discordGuildId_data: int, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                register_select_all_result = await session.execute(
                    select(tableUser)
                    .where(
                        tableUser.discordGuildId == discordGuildId_data,
                        tableUser.serverRegionFK == region,
                    )
                    .order_by(tableUser.albionNick)
                )
            finally:
                await session.close()

        return register_select_all_result.scalars()


async def registerSelectAllDiscordByGuildName(
    discordGuildId_data: int, albionGuildName_data: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                query = (
                    select(tableUser)
                    .where(
                        tableUser.discordGuildId == discordGuildId_data,
                        tableUser.registerGuild == albionGuildName_data,
                        tableUser.serverRegionFK == region,
                    )
                    .order_by(tableUser.albionNick)
                )
                query_result = await session.execute(query)
            finally:
                await session.close()

        return query_result.scalars()


class tableBlacklist(Base):
    __tablename__ = mysql_table_blacklist
    __table_args__ = {"extend_existing": True}

    discordGuildId = Column(
        VARCHAR(19),
        ForeignKey(f"{mysql_table_config}.discordGuildId", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    blacklistId = Column(VARCHAR(23), primary_key=True, autoincrement=False)
    blacklistAOName = Column(VARCHAR(25))
    blacklistDate = Column(VARCHAR(19))
    blacklistById = Column(VARCHAR(19))
    blacklistByNickname = Column(VARCHAR(33))
    blacklistType = Column(VARCHAR(7))
    blacklistReason = Column(VARCHAR(150))
    serverRegionFK = Column(
        VARCHAR(19), ForeignKey(f"{mysql_table_region}.serverRegion")
    )


async def blacklistInsert(
    discordGuildId_data: int,
    blacklistId_data: int,
    blacklistAOName_data: str,
    blacklistDate_data: str,
    blacklistById_data: int,
    blacklistByNickname_data: str,
    blacklistType_data: str,
    blacklistReason_data: str,
    region: str,
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )
    async with async_session() as session:
        async with session.begin():
            check_blacklist_table = select(tableBlacklist).filter_by(
                discordGuildId=discordGuildId_data,
                blacklistId=blacklistId_data,
                serverRegionFK=region,
            )
            check_blacklist_table_query = await session.execute(check_blacklist_table)
            check_blacklist_table_result = check_blacklist_table_query.scalars().first()

            try:
                if check_blacklist_table_result == None:
                    session.add_all(
                        [
                            tableBlacklist(
                                discordGuildId=discordGuildId_data,
                                blacklistId=blacklistId_data,
                                blacklistAOName=blacklistAOName_data,
                                blacklistDate=blacklistDate_data,
                                blacklistById=blacklistById_data,
                                blacklistByNickname=blacklistByNickname_data,
                                blacklistType=blacklistType_data,
                                blacklistReason=blacklistReason_data,
                                serverRegionFK=region,
                            ),
                        ]
                    )
                    await session.commit()
                else:
                    blacklist_update = (
                        update(tableBlacklist)
                        .where(
                            tableBlacklist.discordGuildId == discordGuildId_data,
                            tableBlacklist.blacklistAOName == blacklistAOName_data,
                            tableBlacklist.serverRegionFK == region,
                        )
                        .values(
                            blacklistAOName=blacklistAOName_data,
                            blacklistDate=blacklistDate_data,
                            blacklistById=blacklistById_data,
                            blacklistByNickname=blacklistByNickname_data,
                            blacklistReason=blacklistReason_data,
                            serverRegionFK=region,
                        )
                    )
                    await session.execute(blacklist_update)
                    await session.commit()
            finally:
                await session.close()


async def blacklistDelete(discordGuildId_data: int, albionOnlineId: str, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            blacklist_delete = delete(tableBlacklist).where(
                tableBlacklist.discordGuildId == discordGuildId_data,
                tableBlacklist.blacklistId == albionOnlineId,
                tableBlacklist.serverRegionFK == region,
            )

            try:
                await session.execute(blacklist_delete)
                await session.commit()

            finally:
                await session.close()


async def blacklistDeleteByTypeName(
    discordGuildId_data: int, blacklist_type_data: int, blacklistName: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            blacklist_delete = delete(tableBlacklist).where(
                tableBlacklist.discordGuildId == discordGuildId_data,
                tableBlacklist.blacklistType == blacklist_type_data,
                tableBlacklist.blacklistAOName == blacklistName,
                tableBlacklist.serverRegionFK == region,
            )

            try:
                await session.execute(blacklist_delete)
                await session.commit()

            finally:
                await session.close()


async def blacklistSelectAll(discordGuildId_data: int, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                register_select_all_result = await session.execute(
                    select(tableBlacklist)
                    .where(
                        tableBlacklist.discordGuildId == discordGuildId_data,
                        tableBlacklist.serverRegionFK == region,
                    )
                    .order_by(tableBlacklist.blacklistAOName)
                )
            finally:
                await session.close()

        return register_select_all_result.scalars()


async def blacklistSelectAllByType(
    discordGuildId_data: int, type_data: str, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            try:
                register_select_all_result = await session.execute(
                    select(tableBlacklist).where(
                        tableBlacklist.discordGuildId == discordGuildId_data,
                        tableBlacklist.blacklistType == type_data,
                        tableBlacklist.serverRegionFK == region,
                    )
                )
            finally:
                await session.close()

        return register_select_all_result.scalars()


async def blacklistSelectByType(
    discordGuildId: int, blacklistName: str, blacklistType: int, region: str
):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            blacklist_select_type = select(tableBlacklist).where(
                tableBlacklist.discordGuildId == discordGuildId,
                tableBlacklist.blacklistType == blacklistType,
                tableBlacklist.blacklistAOName == blacklistName,
                tableBlacklist.serverRegionFK == region,
            )
            try:
                result = await session.execute(blacklist_select_type)
            finally:
                await session.close()

        return result.scalar()


async def blacklistSelectId(discordGuildId: int, blacklistId: str, region: str):
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, future=True
    )

    async with async_session() as session:
        async with session.begin():
            blacklist_select_id = select(tableBlacklist).where(
                tableBlacklist.discordGuildId == discordGuildId,
                tableBlacklist.blacklistId == blacklistId,
                tableBlacklist.serverRegionFK == region,
            )
            try:
                result = await session.execute(blacklist_select_id)
            finally:
                await session.close()

        return result.scalar()


async def tables_creation():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()
