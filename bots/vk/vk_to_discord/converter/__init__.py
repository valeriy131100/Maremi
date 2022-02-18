import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import disnake as discord
import vkbottle.bot
from vkbottle.tools.dev.mini_types.base.message import Mention
from vkbottle_types.objects import (AudioAudio, MessagesMessageAttachment,
                                    WallCommentAttachment,
                                    WallWallpostAttachment)

import bots
import freeimagehost
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_channel_send_webhook
from bots.vk.utils import get_photo_max_size
from models import MessageToMessage, Server

from .get_from import get_from_info
from .music import process_audios
from .post_like import make_comment_embed, make_post_embed

DOC_GIF_TYPE = 3
DOC_IMAGE_TYPE = 4

EMBED_TYPE_NULL = 'embed_type_null'
EMBED_TYPE_POST = 'embed_type_post'
EMBED_TYPE_BASIC = 'embed_type_basic'
EMBED_TYPE_COMMENT = 'embed_type_comment'

MENTION_LINK = '[{text}](https://vk.com/{id_type}{id_value})'
MENTION_REGEX = re.compile(r'\[(id|club|public)(\d+)\|([^\]]*)\]')

DISCORD_MESSAGE_LINK = (
    'https://discord.com/channels/{server_id}/{channel_id}/{message_id}'
)


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


async def process_attachments(attachments: List[
    Union[
        MessagesMessageAttachment,
        WallWallpostAttachment,
        WallCommentAttachment
    ]
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
            elif post_comment := attachment.wall_reply:
                media.embed_type = EMBED_TYPE_COMMENT
                media.embed_args = (post_comment,)
                if post_comment.attachments:
                    comment_media = (
                        await process_attachments(post_comment.attachments)
                    )
                    media.extend(comment_media)

    return media


async def process_images(images, embed: discord.Embed,
                         buttons: discord.ui.View):
    images_count = len(images)
    if images_count == 0:
        return [embed] if embed else [], buttons
    elif images_count == 1:
        embed.set_image(images[0])
        return [embed], buttons
    elif images_count > 1:
        embeds, buttons = await create_gallery(
            images,
            embed=embed,
            upload=False,
            use_multiple_preview=True,
            buttons=buttons
        )
        return embeds, buttons


async def process_files(files, embed: discord.Embed):
    if files:
        docs = '\n'.join([f'[{doc_name}]({doc_url})'
                          for doc_name, doc_url in files.items()])
        embed.add_field(
            name='Документы',
            value=docs,
            inline=False
        )

    return embed


def handle_mention(match: re.Match):
    groups = match.groups()
    return MENTION_LINK.format(
        text=groups[2],
        id_type=groups[0],
        id_value=groups[1]
    )


async def replace_mentions_as_links(text,
                                    mention: Optional[Mention] = None):
    new_text = ''

    if text:
        new_text = re.sub(
            MENTION_REGEX,
            handle_mention,
            text
        )

    if mention:
        if mention.id < 0:
            mention_link = MENTION_LINK.format(
                text=mention.text,
                id_type='club',
                id_value=abs(mention.id)
            )
        else:
            mention_link = MENTION_LINK.format(
                text=mention.text,
                id_type='id',
                id_value=mention.id
            )
        new_text = f'{mention_link}, {new_text}'

    return new_text


async def process_all(media: ProcessedAttachments,
                      embed: Optional[discord.Embed],
                      buttons: discord.ui.View):
    media.images.extend(
        await freeimagehost.multiple_upload_and_get_url(media.gif_images)
    )

    embed = await process_files(media.files, embed)
    embed = await process_audios(media.audios, embed)

    if embed:
        embed.description = await replace_mentions_as_links(embed.description)

    embeds, buttons = await process_images(media.images, embed, buttons)

    return embeds, buttons


async def get_discord_message(vk_message: vkbottle.bot.Message,
                              for_edit=False):
    media = await process_attachments(vk_message.attachments)
    embed = None
    text = await replace_mentions_as_links(
        vk_message.text,
        vk_message.mention if not for_edit else None
    )
    buttons = discord.ui.View()

    if media.embed_type == EMBED_TYPE_POST:
        embed, buttons = await make_post_embed(*media.embed_args)
    elif media.embed_type == EMBED_TYPE_BASIC:
        embed = await make_basic_embed(vk_message)
    elif media.embed_type == EMBED_TYPE_COMMENT:
        embed, buttons = await make_comment_embed(*media.embed_args)

    embeds, buttons = await process_all(media, embed, buttons)

    if reply_message := vk_message.reply_message:
        if reply_message.text:
            server = await Server.get(chat_id=vk_message.chat_id)
            discord_message = await MessageToMessage.get_or_none(
                server=server,
                vk_message_id=reply_message.conversation_message_id
            )
            lines = reply_message.text.split('\n')
            formatted_lines = ''.join(f'> {line}\n' for line in lines)

            if not discord_message:
                text = f'{formatted_lines}{text}'
            else:
                message_link = DISCORD_MESSAGE_LINK.format(
                    server_id=server.server_id,
                    channel_id=discord_message.channel_id,
                    message_id=discord_message.discord_message_id
                )

                text = (
                    f'> [Сообщение]({message_link})\n{formatted_lines}{text}'
                )

    if for_edit:
        return {
            'content': text,
            'embeds': embeds,
            'view': buttons
        }
    else:
        from_info = await get_from_info(vk_message.from_id)
        await from_info.load_nickname()

        return {
            'content': text,
            'embeds': embeds,
            'avatar_url': from_info.avatar_url,
            'username': from_info.nickname,
            'view': buttons
        }


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message):
    channel = bots.discord_bot.get_channel(channel_id)
    webhook = await get_channel_send_webhook(channel)
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

