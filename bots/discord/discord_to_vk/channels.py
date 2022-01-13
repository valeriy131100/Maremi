from disnake.ext import commands
from tortoise.exceptions import DoesNotExist

from models import Server, ServerChannelAlias


class DiscordToVkChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def alias(self, context: commands.Context, alias_word):
        server = await Server.get(server_id=context.guild.id)
        is_always_created = await ServerChannelAlias.filter(
            channel_id=context.channel.id,
            alias=alias_word
        )
        if is_always_created:
            await context.send(f'Подобный алиас уже существует.'
                               f' Используйте {context.prefix}alias remove')
            return

        await ServerChannelAlias.create(
            server=server,
            channel_id=context.channel.id,
            alias=alias_word
        )
        await context.send(f'Алиас {alias_word} для канала был создан. '
                           f'Используйте #{alias_word} в вк-боте, '
                           f'чтобы слать сюда сообщения.')

    @alias.command(name='remove')
    async def remove_alias(self, context: commands.Context, alias_word):
        try:
            server = await Server.get(server_id=context.guild.id)
            alias = await ServerChannelAlias.get(
                server=server,
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
