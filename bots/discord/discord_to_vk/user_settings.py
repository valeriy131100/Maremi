from disnake.ext import commands

from bots.discord import CommandInteraction
from models import DiscordUser


class DiscordToVkUserSettings(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def nickname(self, inter: CommandInteraction) -> None:
        """
        Nickname management {{NICKNAME}}
        """

    @nickname.sub_command()
    async def set(self, inter: CommandInteraction, nickname: str) -> None:
        """
        Set VK nickname {{NICKNAME_SET}}

        Parameters
        ----------
        inter: ...
        nickname: Nickname {{NICKNAME_NICKNAME}}
        """
        await DiscordUser.update_or_create(
            discord_id=inter.author.id,
            defaults={
                "nickname": nickname
            }
        )
        await inter.ephemeral("Никнейм успешно изменён")

    @nickname.sub_command()
    async def remove(self, inter: CommandInteraction) -> None:
        """
        Delete VK nickname {{NICKNAME_DELETE}}
        """
        await DiscordUser.update_or_create(
            discord_id=inter.author.id,
            defaults={
                "nickname": ""
            }
        )
        await inter.ephemeral("Никнейм успешно удален")
