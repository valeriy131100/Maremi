import disnake as discord
from disnake.ext import commands

NOTHING = 'nothing'


class NothingHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, interaction: discord.MessageInteraction):
        if interaction.component.custom_id.startswith(NOTHING):
            await interaction.response.defer()
