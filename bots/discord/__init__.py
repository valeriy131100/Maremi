import aiofiles
from disnake.ext import commands
from .discord_to_vk import DiscordToVk
from .image_working import ImageWorking

discord_bot = commands.Bot(command_prefix='m.', help_command=None)
discord_bot.add_cog(DiscordToVk(discord_bot))
discord_bot.add_cog(ImageWorking(discord_bot))


@discord_bot.command(name='help')
async def help_(context: commands.Context):
    async with aiofiles.open('discord_help_message.txt', mode='r', encoding='utf-8') as help_file:
        help_text = await help_file.read()
        await context.send(help_text)
