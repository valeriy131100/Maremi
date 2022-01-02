import bots
from models import Server
from disnake.ext import commands


class DiscordToVkConnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def connect(self, context: commands.Context, chat_id):
        try:
            chat_id = int(chat_id)
        except ValueError:
            await context.send(f'Это не id чата Вконтакте')
        else:
            if bots.temp['chats'].get(chat_id, False):
                await Server.create(
                    server_id=context.guild.id,
                    chat_id=chat_id,
                    default_channel=context.channel.id
                )
                await context.send(f'Сервер {context.guild.id} успешно привязан к чату {chat_id}')
                await context.send(f'Канал по умолчанию установлен на текущий ({context.channel.id})')
            else:
                await context.channel.send(f'Чат {chat_id} не разрешил себя привязывать')
