from disnake.ext import commands

import bots
from bots.discord.utils.wrappers import react_success_and_delete
from bots.exceptions import ChatNotAllowed
from models import Server


class DiscordToVkConnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @react_success_and_delete(exceptions=ChatNotAllowed)
    async def connect(self, context: commands.Context, chat_id: int):
        if bots.temp['chats'].get(chat_id, False):
            await Server.create(
                server_id=context.guild.id,
                chat_id=chat_id,
                default_channel=context.channel.id
            )
        else:
            raise ChatNotAllowed(chat_id)
