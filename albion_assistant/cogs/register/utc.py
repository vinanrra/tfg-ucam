from datetime import datetime, timezone

import nextcord
from nextcord import Interaction
from nextcord.ext import commands


class utcCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command(description="Get utc time")
    async def utc(
        self,
        interaction: Interaction,
    ):
        now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")

        utcTime = nextcord.Embed(description=f"⏰ UTC time now: **{now_utc}**")

        await interaction.response.send_message(embed=utcTime)


def setup(bot):
    bot.add_cog(utcCog(bot))
