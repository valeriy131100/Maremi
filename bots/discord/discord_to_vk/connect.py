from disnake import Localized
from disnake.ext import commands

import bots
from bots.discord import CommandInteraction
from models import Server


class DiscordToVkConnect(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command()
    @commands.default_member_permissions(manage_guild=True)
    async def connect(self,
                      inter: CommandInteraction,
                      chat: int) -> None:
        """
        Connect chat to server {{CONNECT}}

        Parameters
        ----------
        inter: ...
        chat: chat for connect {{CHAT}}
        """
        if bots.temp['chats'].get(chat, False):
            if inter.db_server:
                await inter.db_server.delete()
            await Server.create(
                server_id=inter.guild.id,
                chat_id=chat,
                default_channel=inter.channel.id
            )
            await inter.ephemeral("Сервер успешно подключен к чату")
            return
        await inter.ephemeral("Чат не разрешал себя подключать")
        return

    @commands.slash_command(description="Отключает сервер от чата")
    @commands.default_member_permissions(manage_guild=True)
    async def disconnect(self, inter: CommandInteraction) -> None:
        """
        Disconnect chat from server {{DISCONNECT}}
        """
        await inter.db_server.delete()
        await inter.ephemeral("Сервер успешно отключен от чата")
        return
