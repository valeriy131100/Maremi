import disnake as discord
from disnake.ext import commands

import config
from bots.help_message_formatter import format_help_message

from .discord_to_vk import DiscordToVk
from .image_working import ImageWorking
from .utils import Utils

discord_bot = commands.Bot(
    command_prefix=config.discord_prefix,
    help_command=None
)
discord_bot.add_cog(DiscordToVk(discord_bot))
discord_bot.add_cog(ImageWorking(discord_bot))
discord_bot.add_cog(Utils(discord_bot))


@discord_bot.command(name='help')
async def help_(context: commands.Context):
    help_text = await format_help_message('discord_help_message.txt')
    embed = discord.Embed(title='Список команд', description=help_text)
    await context.send(embed=embed)
