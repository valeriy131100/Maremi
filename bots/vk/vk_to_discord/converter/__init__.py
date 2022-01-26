from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Union

import disnake
import disnake as discord
import vkbottle.bot
from vkbottle_types.objects import (AudioAudio, MessagesMessageAttachment,
                                    WallWallpostAttachment)

import bots
import freeimagehost
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_or_create_channel_send_webhook
from bots.vk.utils import get_photo_max_size
from models import MessageToMessage, Server, VkNickName

from .music import process_audios
from .wallpost import make_post_embed

DOC_GIF_TYPE = 3
DOC_IMAGE_TYPE = 4

EMBED_TYPE_NULL = 'embed_type_null'
EMBED_TYPE_POST = 'embed_type_post'
EMBED_TYPE_BASIC = 'embed_type_basic'


@dataclass
class ProcessedAttachments:
    images: List[str] = field(default_factory=list)
    gif_images: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)
    audios: List[AudioAudio] = field(default_factory=list)
    embed_type: str = EMBED_TYPE_NULL
    embed_args: List[Any] = field(default_factory=list)

    def extend(self, other):
        self.images.extend(other.images)
        self.gif_images.extend(other.gif_images)
        self.audios.extend(other.audios)
        self.files = {**self.files, **other.files}


async def make_basic_embed(vk_message: vkbottle.bot.Message, text=None):
    timestamp = datetime.utcfromtimestamp(vk_message.date)
    if text:
        embed = discord.Embed(description=text, timestamp=timestamp)
    else:
        embed = discord.Embed(timestamp=timestamp)

    return embed


async def get_user_info_from_vk_message(vk_message: vkbottle.bot.Message):
    user = await vk_message.get_user(fields=['photo_50'])
    user_nickname = (await VkNickName.get_or_none(vk_id=user.id))
    if user_nickname:
        username = (f'{user_nickname.nickname} '
                    f'({user.first_name} {user.last_name})')
    else:
        username = f'{user.first_name} {user.last_name}'

    avatar_url = f'{user.photo_50}'

    return username, avatar_url


async def process_attachments(attachments: List[
    Union[MessagesMessageAttachment, WallWallpostAttachment]
]):
    media = ProcessedAttachments()
    for attachment in attachments:
        if photo := attachment.photo:
            media.embed_type = EMBED_TYPE_BASIC
            photo_size = get_photo_max_size(photo.sizes)
            media.images.append(photo_size.url)
        elif doc := attachment.doc:
            media.embed_type = EMBED_TYPE_BASIC
            if doc.type == DOC_IMAGE_TYPE:
                media.images.append(doc.url)
            elif doc.type == DOC_GIF_TYPE:
                media.gif_images.append(doc.url)
            else:
                media.files[doc.title] = doc.url
        elif audio := attachment.audio:
            media.embed_type = EMBED_TYPE_BASIC
            media.audios.append(audio)
        elif isinstance(attachment, MessagesMessageAttachment):
            if sticker := attachment.sticker:
                media.embed_type = EMBED_TYPE_BASIC
                for size in sticker.images:
                    if size.width == 128:
                        size_128 = size
                        media.images.append(size_128.url)
                break  # sticker always unique
            elif post := attachment.wall:
                media.embed_type = EMBED_TYPE_POST
                media.embed_args = (post,)
                if post.attachments:
                    post_media = (
                        await process_attachments(post.attachments)
                    )
                    media.extend(post_media)

    return media


async def process_images(images, embed: disnake.Embed):
    images_count = len(images)
    if images_count == 0:
        buttons = discord.ui.View()
        return [embed] if embed else [], buttons
    elif images_count == 1:
        embed.set_image(images[0])
        buttons = discord.ui.View()
        return [embed], buttons
    elif images_count > 1:
        embeds, buttons = await create_gallery(
            images,
            embed=embed,
            upload=False,
            invite_mode=True,
            use_multiple_preview=True
        )
        return embeds, buttons


async def process_files(files, embed: disnake.Embed):
    if files:
        docs = '\n'.join([f'[{doc_name}]({doc_url})'
                          for doc_name, doc_url in files.items()])
        embed.add_field(
            name='Документы',
            value=docs,
            inline=False
        )

    return embed


async def get_discord_message(vk_message: vkbottle.bot.Message):

    username, avatar_url = await get_user_info_from_vk_message(vk_message)
    media = await process_attachments(vk_message.attachments)
    embed = None
    text = vk_message.text

    if media.embed_type == EMBED_TYPE_POST:
        embed = await make_post_embed(*media.embed_args)
    elif media.embed_type == EMBED_TYPE_BASIC:
        embed = await make_basic_embed(vk_message)

    media.images.extend(
        await freeimagehost.multiple_upload_and_get_url(media.gif_images)
    )

    embed = await process_files(media.files, embed)
    embed = await process_audios(media.audios, embed)

    embeds, buttons = await process_images(media.images, embed)

    if reply_message := vk_message.reply_message:
        if reply_message.text:
            lines = reply_message.text.split('\n')
            formatted_lines = ''.join(f'> {line}\n' for line in lines)
            text = f'{formatted_lines}{text}'

    return {
        'content': text,
        'embeds': embeds,
        'avatar_url': avatar_url,
        'username': username,
        'view': buttons,
    }


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message):
    channel = bots.discord_bot.get_channel(channel_id)
    webhook = await get_or_create_channel_send_webhook(channel)
    discord_message = await webhook.send(
        wait=True,
        **(await get_discord_message(vk_message))
    )
    server = await Server.get(server_id=discord_message.guild.id)

    await MessageToMessage.create(
        server=server,
        channel_id=discord_message.channel.id,
        vk_message_id=vk_message.conversation_message_id,
        discord_message_id=discord_message.id,
        vk_timestamp=vk_message.date
    )

