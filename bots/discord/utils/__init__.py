from disnake.ext import commands

from .galleries import GalleriesHandler


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_cog(GalleriesHandler(bot))
