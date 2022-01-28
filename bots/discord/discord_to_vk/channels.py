import tortoise.exceptions
from disnake.ext import commands
from tortoise.exceptions import DoesNotExist, IntegrityError

from models import Server, ServerChannelAlias


class DiscordToVkChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def alias(self, context: commands.Context, alias_word):
        try:
            await ServerChannelAlias.create(
                server_id=context.guild.id,
                channel_id=context.channel.id,
                alias=alias_word
            )
        except IntegrityError:
            await context.send(f'Подобный алиас уже существует.'
                               f' Используйте {context.prefix}alias remove')
            return
        else:
            await context.send(f'Алиас {alias_word} для канала был создан. '
                               f'Используйте #{alias_word} в вк-боте, '
                               f'чтобы слать сюда сообщения.')

    @alias.command(name='remove')
    async def remove_alias(self, context: commands.Context, alias_word):
        try:
            alias = await ServerChannelAlias.get(
                server_id=context.guild.id,
                alias=alias_word
            )
            await alias.delete()
        except DoesNotExist:
            await context.send(f'Алиас не найден')
        else:
            await context.send(f'Алиас {alias_word} успешно удален')

    @commands.command(name='default')
    async def set_default(self, context: commands.Context):
        server = await Server.get(server_id=context.guild.id)
        server.server_default_channel = context.channel.id
        await server.save()
        await context.send(f'Текущий канал установлен как канал по умолчанию')

    @commands.command(name='art')
    async def set_art(self, context: commands.Context):
        server = await Server.get(server_id=context.guild.id)
        server.default_image_channel = context.channel.id
        await server.save()
        await context.send(f'Текущий канал установлен как канал по умолчанию для изображений')

    @commands.command(name='duplex')
    async def set_duplex(self, context: commands.Context):
        server = await Server.get(server_id=context.guild.id)
        server.duplex_channel = context.channel.id
        await server.save()
        await context.send(f'Текущий канал установлен как дуплексный канал')
