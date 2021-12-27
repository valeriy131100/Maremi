import os
import disnake as discord
from vkbottle import PhotoMessageUploader
import bots
import db_helpers
from bots.discord.utils.emojis import EMOJI_REGEX, download_file, download_emoji
from bots.vk.utils import get_random_id


async def get_vk_message(discord_message: discord.Message):
    nickname = await db_helpers.get_discord_nickname(discord_message.author.id)
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
        author_string = f'{nickname} ({discord_message.author}):'
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
    await bots.vk_bot.api.messages.send(
        chat_id=chat_id,
        **(await get_vk_message(discord_message))
    )
