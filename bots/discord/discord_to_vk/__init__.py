import disnake as discord
import db_helpers
from disnake.ext import commands
from bots.discord.utils.webhooks import get_server_bot_webhooks_ids
from .converter import send_to_vk
from .channels import DiscordToVkChannels
from .user_settings import DiscordToVkUserSettings
from .connect import DiscordToVkConnect


class DiscordToVk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_cog(DiscordToVkChannels(bot))
        bot.add_cog(DiscordToVkUserSettings(bot))
        bot.add_cog(DiscordToVkConnect(bot))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        webhooks = await get_server_bot_webhooks_ids(message.guild)
        if ((await db_helpers.is_duplex_channel(message.guild.id, message.channel.id))
                and not message.author == self.bot.user
                and not message.content.startswith(self.bot.command_prefix)
                and message.webhook_id not in webhooks):
            chat_id = await db_helpers.get_server_chat(message.guild.id)
            await send_to_vk(chat_id, message)
