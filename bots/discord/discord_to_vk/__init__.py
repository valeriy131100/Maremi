import disnake as discord
import bots
import db_helpers
from disnake.ext import commands
from .converter import send_to_vk
from .channels import DiscordToVkChannels
from .user_settings import DiscordToVkUserSettings


class DiscordToVk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_cog(DiscordToVkChannels(bot))
        bot.add_cog(DiscordToVkUserSettings(bot))

    @commands.command()
    async def connect(self, context: commands.Context, chat_id):
        try:
            chat_id = int(chat_id)
        except ValueError:
            await context.send(f'Это не id чата Вконтакте')
        else:
            if bots.temp['chats'].get(chat_id, False):
                await db_helpers.connect_server_to_chat(context.guild.id, chat_id, default_channel=context.channel.id)
                await context.send(f'Сервер {context.guild.id} успешно привязан к чату {chat_id}')
                await context.send(f'Канал по умолчанию установлен на текущий ({context.channel.id})')
            else:
                await context.channel.send(f'Чат {chat_id} не разрешил себя привязывать')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if ((await db_helpers.is_duplex_channel(message.guild.id, message.channel.id))
                and not message.author == self.bot.user
                and not message.content.startswith(self.bot.command_prefix)
                and message.webhook_id not in bots.temp['webhooks']):
            chat_id = await db_helpers.get_server_chat(message.guild.id)
            await send_to_vk(chat_id, message)
