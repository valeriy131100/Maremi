import disnake as discord
import bots
from disnake.ext import commands
from bots.discord.utils.webhooks import get_server_bot_webhooks_ids
from models import Server, MessageToMessage
from . import converter
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
        server = await Server.get(server_id=message.guild.id)
        duplex_channel = server.duplex_channel
        if (message.channel.id == duplex_channel
                and not message.author == self.bot.user
                and not message.content.startswith(self.bot.command_prefix)
                and message.webhook_id not in webhooks):

            chat_id = server.chat_id
            await converter.send_to_vk(chat_id, message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        channel = bots.discord_bot.get_channel(
            payload.channel_id
        )
        try:
            discord_message = await channel.fetch_message(
                payload.message_id
            )
        except discord.NotFound:
            return

        guild = discord_message.guild
        webhooks = await get_server_bot_webhooks_ids(guild)
        if discord_message.webhook_id in webhooks:
            return

        message_to_message = await MessageToMessage.get_or_none(
            channel_id=discord_message.channel.id,
            discord_message_id=discord_message.id
        )

        if not message_to_message:
            return

        chat_id = (await message_to_message.server).chat_id

        await bots.vk_bot.api.messages.edit(
            peer_id=2000000000+chat_id,
            conversation_message_id=message_to_message.vk_message_id,
            **(await converter.get_vk_message(discord_message))
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        guild = self.bot.get_guild(payload.guild_id)
        webhooks = await get_server_bot_webhooks_ids(guild)
        if discord_message := payload.cached_message:
            if discord_message.webhook_id in webhooks:
                return

        message_to_message = await MessageToMessage.get_or_none(
            channel_id=payload.channel_id,
            discord_message_id=payload.message_id
        )

        if not message_to_message:
            return

        chat_id = (await message_to_message.server).chat_id

        await bots.vk_bot.api.messages.delete(
            peer_id=2000000000 + chat_id,
            conversation_message_ids=[message_to_message.vk_message_id],
            delete_for_all=True
        )

        await message_to_message.delete()
