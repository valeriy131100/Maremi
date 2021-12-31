import disnake as discord
import config
from disnake.ext import commands
from .discord_to_vk import DiscordToVk
from .image_working import ImageWorking
from .utils import Utils
from bots.help_message_formatter import format_help_message

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
    embed = discord.Embed(title='Список комманд', description=help_text)
    await context.send(embed=embed)
