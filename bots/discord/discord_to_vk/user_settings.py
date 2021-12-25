import db_helpers
from disnake.ext import commands


class DiscordToVkUserSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def nickname(self, context: commands.Context, nickname):
        await db_helpers.set_discord_nickname(context.author.id, nickname)
        await context.send(f'Никнейм {nickname} успешно установлен')

    @nickname.command(name='remove')
    async def remove_nickname(self, context: commands.Context):
        await db_helpers.set_discord_nickname(context.author.id, None)
        await context.send(f'Никнейм успешно удален')
