import disnake
import disnake as discord
import vkbottle.bot
import bots
import db_helpers
import freeimagehost
from vkbottle_types.objects import MessagesMessageAttachment, \
    WallWallpostAttachment
from datetime import datetime
from typing import Union, List, Dict, Any
from dataclasses import dataclass, field
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_or_create_channel_send_webhook
from bots.vk.utils import get_photo_max_size
from .wallpost import make_post_embed


DOC_GIF_TYPE = 3
DOC_IMAGE_TYPE = 4

EMBED_TYPE_POST = 'embed_type_post'
EMBED_TYPE_BASIC = 'embed_type_basic'


@dataclass
class ProcessedAttachments:
    images: List[str] = field(default_factory=list)
    gif_images: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)
    embed_type: str = EMBED_TYPE_BASIC
    embed_args: List[Any] = field(default_factory=list)


async def make_basic_embed(vk_message: vkbottle.bot.Message, text=None):
    timestamp = datetime.utcfromtimestamp(vk_message.date)
    if text:
        embed = discord.Embed(description=text, timestamp=timestamp)
    else:
        embed = discord.Embed(timestamp=timestamp)

    return embed


async def get_user_info_from_vk_message(vk_message: vkbottle.bot.Message):
    user = await vk_message.get_user(fields=['photo_50'])
    user_nickname = await db_helpers.get_vk_nickname(user.id)
    if user_nickname:
        username = f'{user_nickname} ({user.first_name} {user.last_name})'
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
            photo_size = get_photo_max_size(photo.sizes)
            media.images.append(photo_size.url)
        elif doc := attachment.doc:
            if doc.type == DOC_IMAGE_TYPE:
                media.images.append(doc.url)
            elif doc.type == DOC_GIF_TYPE:
                media.gif_images.append(doc.url)
            else:
                media.files[doc.title] = doc.url
        elif sticker := attachment.sticker:
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
                media.images.extend(post_media.images)
                media.gif_images.extend(post_media.gif_images)
                media.files = {**media.files, **post_media.files}

    return media


async def process_images(images, embed: disnake.Embed):
    images_count = len(images)
    if images_count == 0:
        buttons = discord.ui.View()
        return embed, buttons
    elif images_count == 1:
        embed.set_image(images[0])
        buttons = discord.ui.View()
        return embed, buttons
    elif images_count > 1:
        embed, buttons = await create_gallery(
            images,
            embed=embed,
            upload=False
        )
        return embed, buttons


async def process_files(files, embed: disnake.Embed):
    if files:
        docs = ''
        for doc_name, doc_url in files.items():
            docs = (f'{docs}\n'
                    f'[{doc_name}]({doc_url})')
        embed.add_field(
            name='Документы',
            value=docs
        )

    return embed


async def get_discord_message(vk_message: vkbottle.bot.Message):

    username, avatar_url = await get_user_info_from_vk_message(vk_message)
    media = await process_attachments(vk_message.attachments)

    if media.embed_type == EMBED_TYPE_POST:
        embed = await make_post_embed(*media.embed_args)
    else:
        embed = await make_basic_embed(vk_message)

    media.images.extend(
        await freeimagehost.multiple_upload_and_get_url(media.gif_images)
    )

    embed = await process_files(media.files, embed)
    embed, buttons = await process_images(media.images, embed)

    return {
        'content': vk_message.text,
        'embed': embed,
        'avatar_url': avatar_url,
        'username': username,
        'view': buttons
    }


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message):
    channel = bots.discord_bot.get_channel(channel_id)
    webhook = await get_or_create_channel_send_webhook(channel)
    discord_message = await webhook.send(
        wait=True,
        **(await get_discord_message(vk_message))
    )
    await db_helpers.save_message(
        server_id=discord_message.guild.id,
        channel_id=channel_id,
        chat_id=vk_message.chat_id,
        vk_message_id=vk_message.conversation_message_id,
        discord_message_id=discord_message.id,
        timestamp=vk_message.date
    )

