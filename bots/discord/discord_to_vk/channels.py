from sqlite3 import IntegrityError
from disnake.ext import commands
import db_helpers


class DiscordToVkChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def alias(self, context: commands.Context, alias_word):
        try:
            await db_helpers.make_alias(context.guild.id, context.channel.id, alias_word)
            await context.send(f'Алиас {alias_word} для канала был создан. Используйте #{alias_word} в вк-боте, '
                               f'чтобы слать сюда сообщения.')
        except IntegrityError:
            await context.send(f'Подобный алиас уже существует. Используйте {context.prefix}removealias')

    @alias.command(name='remove')
    async def remove_alias(self, context: commands.Context, alias_word):
        try:
            await db_helpers.delete_alias(context.guild.id, alias_word)
        except IndexError:
            await context.send(f'Алиас не найден')
        else:
            await context.send(f'Алиас {alias_word} успешно удален')

    @commands.command(name='default')
    async def set_default(self, context: commands.Context):
        await db_helpers.set_default_channel(server_id=context.guild.id, channel_id=context.channel.id)
        await context.send(f'Текущий канал установлен как канал по умолчанию')

    @commands.command(name='art')
    async def set_art(self, context: commands.Context):
        await db_helpers.set_default_image_channel(server_id=context.guild.id, channel_id=context.channel.id)
        await context.send(f'Текущий канал установлен как канал по умолчанию для изображений')

    @commands.command(name='duplex')
    async def set_duplex(self, context: commands.Context):
        await db_helpers.set_duplex_channel(server_id=context.guild.id, channel_id=context.channel.id)
        await context.send(f'Текущий канал установлен как дуплексный канал')
