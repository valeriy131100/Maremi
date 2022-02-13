from disnake.ext import commands
from tortoise.exceptions import DoesNotExist, IntegrityError

from bots.discord.utils.wrappers import react_success_and_delete
from models import Server, ServerChannelAlias


class DiscordToVkChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    @react_success_and_delete(exception=IntegrityError)
    async def alias(self, context: commands.Context, alias_word):
        await ServerChannelAlias.create(
            server_id=context.guild.id,
            channel_id=context.channel.id,
            alias=alias_word
        )

    @alias.command(name='remove')
    @react_success_and_delete(exception=DoesNotExist)
    async def remove_alias(self, context: commands.Context, alias_word):
        alias = await ServerChannelAlias.get(
            server_id=context.guild.id,
            alias=alias_word
        )
        await alias.delete()

    @commands.command(name='default')
    @react_success_and_delete
    async def set_default(self, context: commands.Context):
        server = await Server.get(server_id=context.guild.id)
        server.server_default_channel = context.channel.id
        await server.save()

    @commands.command(name='art')
    @react_success_and_delete
    async def set_art(self, context: commands.Context):
        server = await Server.get(server_id=context.guild.id)
        server.default_image_channel = context.channel.id
        await server.save()

    @commands.command(name='duplex')
    @react_success_and_delete
    async def set_duplex(self, context: commands.Context):
        server = await Server.get(server_id=context.guild.id)
        server.duplex_channel = context.channel.id
        await server.save()
