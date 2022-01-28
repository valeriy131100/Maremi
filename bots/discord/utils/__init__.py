from disnake.ext import commands

from .galleries import GalleriesHandler
from .nothing_buttons import NothingHandler


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_cog(GalleriesHandler(bot))
        bot.add_cog(NothingHandler(bot))
