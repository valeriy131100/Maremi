import traceback

import disnake as discord
from disnake import Intents, errors, InteractionResponded, InteractionNotResponded, NotFound
from disnake.ext.commands import CommandError

import config
from bots.help_message_formatter import format_help_message
from models import Server

from .discord_to_vk import DiscordToVk
from .image_working import ImageWorking
from .base import CommandInteraction, Bot
from .utils import Utils

intents = Intents.all()

discord_bot = Bot(
    command_prefix=config.discord_prefix,
    help_command=None,
    intents=intents,
    test_guilds=config.test_guilds
)
discord_bot.i18n.load("bots/discord/locale/")
discord_bot.add_cog(DiscordToVk(discord_bot))
discord_bot.add_cog(ImageWorking(discord_bot))
discord_bot.add_cog(Utils(discord_bot))


@discord_bot.slash_command_check
async def prepare_slash_command(inter: CommandInteraction) -> bool:
    command_name = inter.application_command.name

    await inter.load_db_server()
    if inter.db_server:
        return True

    if command_name == 'connect':
        return True

    await inter.ephemeral("Для начала присоедините сервер к чату командой /connect")
    return False


@discord_bot.event
async def on_slash_command_error(inter: CommandInteraction, exception: CommandError):
    try:
        await inter.response.defer(with_message=True, ephemeral=True)
    except InteractionResponded:
        pass
    finally:
        try:
            await inter.edit_original_response("Произошла непредвиденная ошибка", view=None, suppress_embeds=True)
        except NotFound:
            await inter.followup.send("Произошла непредвиденная ошибка", ephemeral=True)

    if inter.user.id in config.devs:
        formatted_exception = "\n".join(traceback.format_exception(exception))
        await inter.followup.send(f"Ошибка:\n```\n{formatted_exception}```", ephemeral=True)

    traceback.print_exception(exception)


@discord_bot.slash_command(name='help', description="Выводит список команд")
async def help_(inter: CommandInteraction) -> None:
    help_text = await format_help_message("discord_help_message.txt")
    embed = discord.Embed(title="Список команд", description=help_text)
    await inter.send(embed=embed)
