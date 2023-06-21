from disnake.ext import commands

import bots
from bots.discord import CommandInteraction
from models import Server


class DiscordToVkConnect(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(description="Подключает чат к серверу")
    async def connect(self, inter: CommandInteraction, chat_id: int = commands.Param(name="id чата")) -> None:
        if bots.temp['chats'].get(chat_id, False):
            if inter.db_server:
                await inter.db_server.delete()
            await Server.create(
                server_id=inter.guild.id,
                chat_id=chat_id,
                default_channel=inter.channel.id
            )
            await inter.ephemeral("Сервер успешно подключен к чату")
            return
        await inter.ephemeral("Чат не разрешал себя подключать")
        return

    @commands.slash_command(description="Отключает сервер от чата")
    async def disconnect(self, inter: CommandInteraction) -> None:
        await inter.db_server.delete()
        await inter.ephemeral("Сервер успешно отключен от чата")
        return
