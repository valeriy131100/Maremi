import disnake as discord
import db_helpers
import bots
from disnake.ext import commands
from bots.discord.utils.webhooks import get_server_bot_webhooks_ids
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
        if ((await db_helpers.is_duplex_channel(message.guild.id, message.channel.id))
                and not message.author == self.bot.user
                and not message.content.startswith(self.bot.command_prefix)
                and message.webhook_id not in webhooks):
            chat_id = await db_helpers.get_server_chat(message.guild.id)
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
        if discord_message := payload.cached_message:
            if discord_message.webhook_id in webhooks:
                return

        vk_message = await db_helpers.get_vk_message(
            discord_message=discord_message
        )

        if not vk_message:
            return

        chat_id, vk_message_id = vk_message

        await bots.vk_bot.api.messages.edit(
            peer_id=2000000000+chat_id,
            conversation_message_id=vk_message_id,
            **(await converter.get_vk_message(discord_message))
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        guild = self.bot.get_guild(payload.guild_id)
        webhooks = await get_server_bot_webhooks_ids(guild)
        if discord_message := payload.cached_message:
            if discord_message.webhook_id in webhooks:
                return

        vk_message = await db_helpers.get_vk_message(
            guild_id=payload.guild_id,
            channel_id=payload.channel_id,
            message_id=payload.message_id
        )

        if not vk_message:
            return

        chat_id, vk_message_id = vk_message

        await bots.vk_bot.api.messages.delete(
            peer_id=2000000000 + chat_id,
            conversation_message_ids=[vk_message_id],
            delete_for_all=True
        )
