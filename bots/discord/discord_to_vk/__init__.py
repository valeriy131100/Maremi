import disnake as discord
from disnake import HTTPException
from disnake.ext import commands
from tortoise.exceptions import DoesNotExist

import bots
from bots.discord.utils.webhooks import get_server_bot_webhooks_ids
from bots.discord.utils.wrappers import react_success_and_delete
from bots.discord.utils.wrappers.ref_message import NotFoundRef, prefetch_ref
from bots.vk.vk_to_discord import converter as vk_converter
from models import MessageToMessage, Server

from . import converter
from .channels import DiscordToVkChannels
from .connect import DiscordToVkConnect
from .user_settings import DiscordToVkUserSettings


class DiscordToVk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_cog(DiscordToVkChannels(bot))
        bot.add_cog(DiscordToVkUserSettings(bot))
        bot.add_cog(DiscordToVkConnect(bot))

    @commands.command()
    @react_success_and_delete(
        exceptions=(
            NotFoundRef,
            DoesNotExist,
            HTTPException  # fetching webhook error
        )
    )
    @prefetch_ref
    async def reload(self, context: commands.Context):
        ref_message: discord.Message = context.ref_message

        webhook = await self.bot.fetch_webhook(ref_message.webhook_id)

        message_to_message = await MessageToMessage.get(
            channel_id=ref_message.channel.id,
            discord_message_id=ref_message.id
        )

        server = await Server.get(server_id=ref_message.guild.id)

        vk_api = bots.vk_bot.api

        api_answer = await vk_api.messages.get_by_conversation_message_id(
            peer_id=2000000000 + server.chat_id,
            conversation_message_ids=[message_to_message.vk_message_id]
        )

        vk_message = api_answer.items[0]

        discord_message = await vk_converter.get_discord_message(
            vk_message,
            for_edit=True
        )

        await webhook.edit_message(ref_message.id, **discord_message)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        webhooks = await get_server_bot_webhooks_ids(message.guild)
        server = await Server.get(server_id=message.guild.id)
        duplex_channel = server.duplex_channel
        reply_message_to_message = None
        if reply_message := message.reference:
            reply_message_to_message = await MessageToMessage.get_or_none(
                server=server,
                discord_message_id=reply_message.message_id
            )

        need_to_send = ((message.channel.id == duplex_channel)
                        or reply_message_to_message)

        if (need_to_send
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
            keep_forward_messages=1,
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
