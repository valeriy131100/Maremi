from disnake.ext import commands
from models import DiscordNickName


class DiscordToVkUserSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def nickname(self, context: commands.Context, nickname):
        await DiscordNickName.update_or_create(
            discord_id=context.author.id,
            defaults={
                'nickname': nickname
            }
        )
        await context.send(f'Никнейм {nickname} успешно установлен')

    @nickname.command(name='remove')
    async def remove_nickname(self, context: commands.Context):
        await DiscordNickName.update_or_create(
            discord_id=context.author.id,
            defaults={
                'nickname': ''
            }
        )
        await context.send(f'Никнейм успешно удален')
