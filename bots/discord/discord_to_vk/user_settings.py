from disnake.ext import commands

from bots.discord.utils.wrappers import react_success_and_delete
from models import DiscordUser


class DiscordToVkUserSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    @react_success_and_delete
    async def nickname(self, context: commands.Context, nickname):
        await DiscordUser.update_or_create(
            discord_id=context.author.id,
            defaults={
                'nickname': nickname
            }
        )

    @nickname.command(name='remove')
    @react_success_and_delete
    async def remove_nickname(self, context: commands.Context):
        await DiscordUser.update_or_create(
            discord_id=context.author.id,
            defaults={
                'nickname': ''
            }
        )
