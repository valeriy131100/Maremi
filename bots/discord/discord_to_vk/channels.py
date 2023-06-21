from disnake.abc import GuildChannel
from disnake.ext import commands
from tortoise.exceptions import DoesNotExist, IntegrityError

from bots.discord import CommandInteraction
from models import Server, ServerChannelAlias


async def _remove_autocomplete(inter: CommandInteraction, user_input: str) -> list[str]:
    aliases = await ServerChannelAlias.filter(server_id=inter.guild_id).values_list('alias', flat=True)
    return [alias for alias in aliases if user_input in alias]


class DiscordToVkChannels(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command()
    async def alias(self, inter: CommandInteraction) -> None:
        pass

    @alias.sub_command(description="Создает алиас для канала")
    async def create(self,
                     inter: CommandInteraction,
                     name: str,
                     channel: GuildChannel | None = None) -> None:
        if channel is None:
            channel_id = inter.channel_id
        else:
            channel_id = channel.id

        try:
            await ServerChannelAlias.create(
                server_id=inter.guild_id,
                channel_id=channel_id,
                alias=name.lower()
            )
        except IntegrityError:
            await inter.ephemeral("Алиас с таким именем уже создан")
            return
        else:
            await inter.ephemeral("Алиас создан")
            return

    @alias.sub_command(name="remove", description="Удаляет выбранный алиас")
    async def remove(self,
                     inter: CommandInteraction,
                     name: str = commands.Param(autocomplete=_remove_autocomplete)) -> None: # NOQA
        alias = ServerChannelAlias.filter(server_id=inter.guild_id, alias=name)
        if await alias.exists():
            await alias.delete()
            await inter.ephemeral("Алиас успешно удален", ephemeral=True)
            return

        await inter.ephemeral("Алиаса с таким именем не существует", ephemeral=True)
        return

    @commands.slash_command(description="Устанавливает канал для дуплексного режима")
    async def set_duplex(self, inter: CommandInteraction, channel: GuildChannel | None = None) -> None:
        if channel is None:
            channel_id = inter.channel_id
        else:
            channel_id = channel.id

        server = inter.db_server
        if server.exists():
            server.duplex_channel = channel_id
            await server.save()
            await inter.ephemeral("Канал для дуплексного режима успешно установлен")
