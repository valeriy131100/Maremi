from disnake.ext import commands

from bots.discord import CommandInteraction
from models import DiscordUser


class DiscordToVkUserSettings(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def nickname(self, inter: CommandInteraction) -> None:
        pass

    @nickname.sub_command(description="Устанавливает никнейм для отправки сообщений в ВК")
    async def set(self, inter: CommandInteraction, nickname: str = commands.Param(name="никнейм")) -> None:
        await DiscordUser.update_or_create(
            discord_id=inter.author.id,
            defaults={
                "nickname": nickname
            }
        )
        await inter.ephemeral("Никнейм успешно изменён")

    @nickname.sub_command(description="Удаляет никнейм для отправки сообщений в ВК")
    async def remove(self, inter: CommandInteraction) -> None:
        await DiscordUser.update_or_create(
            discord_id=inter.author.id,
            defaults={
                "nickname": ""
            }
        )
        await inter.ephemeral("Никнейм успешно удален")
