import nextcord
from functions.aiohttp import albionApi
from functions.api_process import apiPlayerInfoProcess
from functions.checks import check_api_result

paypal = "https://www.paypal.com/donate/?cmd=_s-xclick&hosted_button_id=25XWMUHD8NZHG"
patreon = "https://www.patreon.com/albionassistantbot"
donations_name = "Support the project:"
donations_value = f"[PayPal]({paypal})\n[Patreon]({patreon})"
support_server = "[Support Server](https://discord.gg/wxaqGTZWXS)"
ao_regions = {"Asia": "East", "Americas": "West", "Europe": "Europe"}

# Confirm/Cancel buttons


class Confirm(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.value = None

    async def on_timeout(self):
        self.clear_items()
        # Message it's assgined outside like this:
        # view.message = await interaction.original_message()
        await self.message.edit(view=self)

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        button.disabled = True
        self.remove_item(self.children[1])
        await interaction.response.edit_message(view=self)
        self.value = True
        self.stop()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(
        self, button: nextcord.ui.Button, interaction: nextcord.Interaction
    ):
        button.disabled = True
        self.remove_item(self.children[0])
        await interaction.response.edit_message(view=self)
        self.value = False
        self.stop()


class DropdownCheck(nextcord.ui.Select):
    def __init__(self, players: dict, region: str):
        self.region = region
        i = 0
        options: list[nextcord.SelectOption] = []
        for player in players["players"]:
            # Set the options that will be presented inside the dropdown
            options.append(
                nextcord.SelectOption(
                    label=f"{i} - {player['Name']}",
                    description=player["Id"],
                    value=player["Id"],
                )
            )

            i = i + 1

        options = options

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Choose the player to show the info...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: nextcord.Interaction):
        # API PLAYER ID SEARCH

        # Ask API
        apiResult = await albionApi("player", self.values[0], self.region)

        # Check result
        checkApiResult = await check_api_result(apiResult["Found"])

        if checkApiResult is not False:
            await interaction.followup.send(embed=checkApiResult)
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

        killboardPlayer = (
            f"https://albiononline.com/en/killboard/player/{apiResultData['Id']}"
        )
        killboardGuild = (
            f"https://albiononline.com/en/killboard/guild/{apiResultData['GuildId']}"
        )
        killboardAlliance = f"https://albiononline.com/en/killboard/alliance/{apiResultData['AllianceId']}"

        if apiResultData["GuildName"] == "":
            guild_url = ""
        else:
            guild_url = f"[{apiResultData['GuildName']}]({killboardGuild})"

        if apiResultData["AllianceName"] == "":
            alliace_url = ""
        else:
            alliace_url = f"[{apiResultData['AllianceName']}]({killboardAlliance})"

        # Embed
        embebCheckPlayer = nextcord.Embed(title="Player Info", color=0x00FF00)
        embebCheckPlayer.add_field(
            name="General Info:",
            value=f"""**IGN:** [{apiResultData['Name']}]({killboardPlayer})
        **Player ID:** ```{apiResultData['Id']}```
        **Guild:** {guild_url}
        **Alliance:** {alliace_url}""",
            inline=True,
        )
        embebCheckPlayer.add_field(
            name="Fame:",
            value=f"""**Total Fame:** {apiResultData['TotalFame']}
        **Death Fame:** {apiResultData['DeathFame']}
        **Kill Fame:** {apiResultData['KillFame']}
        **PvE Fame:** {apiResultData['PvETotalFame']}""",
        )
        embebCheckPlayer.add_field(
            name="Ratio:",
            value=f"""**KDA:** {apiResultData['FameRatio']}
        **PvE:** {apiResultData['PvERatio']}
        **PvP:** {apiResultData['PvPRatio']}""",
        )
        embebCheckPlayer.add_field(
            name="Fame per activity:",
            value=f"""**Crystal Fame:** {apiResultData['CrystalFame']}
        **Royal:** {apiResultData['PvERoyal']}
        **Outlands:** {apiResultData['PvEOutlands']}
        **Avalon:** {apiResultData['Avalon']}
        **Hellgate:** {apiResultData['Hellgate']}
        **Corrupted Dungeon:** {apiResultData['CorruptedDungeon']}
        **Gathering:** {apiResultData['GatheringFame']}
        **Crafting:** {apiResultData['CraftingFame']}
        **Fishing:** {apiResultData['FishingFame']}""",
            inline=True,
        )
        embebCheckPlayer.add_field(
            name=donations_name, value=donations_value, inline=False
        )
        embebCheckPlayer.set_footer(
            text="Support server: https://discord.gg/wxaqGTZWXS"
        )

        self.disabled = True

        await interaction.response.edit_message(embed=embebCheckPlayer, view=None)


class DropdownViewCheck(nextcord.ui.View):
    def __init__(self, players: dict, region: str):
        super().__init__(timeout=180)

        self.add_item(DropdownCheck(players, region))
