from disnake.ext import commands

from bots.discord.utils.wrappers import react_and_delete
from models import DiscordNickName


class DiscordToVkUserSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    @react_and_delete
    async def nickname(self, context: commands.Context, nickname):
        await DiscordNickName.update_or_create(
            discord_id=context.author.id,
            defaults={
                'nickname': nickname
            }
        )

    @nickname.command(name='remove')
    @react_and_delete
    async def remove_nickname(self, context: commands.Context):
        await DiscordNickName.update_or_create(
            discord_id=context.author.id,
            defaults={
                'nickname': ''
            }
        )
