import os
from datetime import datetime

import disnake as discord
from vkbottle import PhotoMessageUploader

import bots
from bots.discord.utils.emojis import (EMOJI_REGEX, download_emoji,
                                       download_file)
from bots.vk.utils import get_random_id
from models import DiscordNickName, MessageToMessage, Server


async def get_vk_message(discord_message: discord.Message):
    nickname = (await DiscordNickName.get_or_none(
        discord_id=discord_message.author.id
    ))
    message_text = discord_message.content
    photo_uploader = PhotoMessageUploader(api=bots.vk_bot.api)
    attachments_list = []

    for full_emoji, is_animated, emoji_id in EMOJI_REGEX.findall(message_text):
        message_text = message_text.replace(full_emoji, '')
        emoji_file = await download_emoji(emoji_id=emoji_id, guild_id=discord_message.guild.id)
        attach = await photo_uploader.upload(file_source=emoji_file)
        os.remove(emoji_file)
        attachments_list.append(attach)
        if len(attachments_list) == 10:
            break

    if nickname:
        author_string = f'{nickname.nickname} ({discord_message.author}):'
    else:
        author_string = f'{discord_message.author}:'
    message_text = f'{author_string}\n{message_text}'

    if attaches := discord_message.attachments:
        for attach in attaches:
            if attach.content_type.startswith('image') and len(attachments_list) != 10:
                image_file = await download_file(url=attach.url, filename=attach.filename)
                attach = await photo_uploader.upload(file_source=image_file)
                os.remove(image_file)
                attachments_list.append(attach)

    attachments = ','.join(attachments_list)

    return {
        'message': message_text,
        'random_id': get_random_id(),
        'attachment': attachments
    }


async def send_to_vk(chat_id, discord_message: discord.Message):
    forward = None
    peer_id = 2000000000 + chat_id

    if reply_message := discord_message.reference:
        reply_message_to_message = await MessageToMessage.get_or_none(
            server__chat_id=chat_id,
            discord_message_id=reply_message.message_id
        )
        if reply_message_to_message:
            reply_to = reply_message_to_message.vk_message_id
            forward = {
                'peer_id': peer_id,
                'conversation_message_ids': [reply_to],
                'is_reply': 1
            }

    vk_message = await bots.vk_bot.api.messages.send(
        peer_ids=[peer_id],
        forward=forward,
        **(await get_vk_message(discord_message))
    )

    vk_message_id = vk_message[0].conversation_message_id

    server = await Server.get(server_id=discord_message.guild.id)

    await MessageToMessage.create(
        server=server,
        channel_id=discord_message.channel.id,
        vk_message_id=vk_message_id,
        discord_message_id=discord_message.id,
        vk_timestamp=int(datetime.now().timestamp())
    )
