import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypedDict

import disnake as discord
import vkbottle.bot
from vkbottle.tools.dev.mini_types.base.message import Mention
from vkbottle_types.objects import (
    AudioAudio,
    MessagesMessageAttachment,
    WallCommentAttachment,
    WallWallpostAttachment,
)

import bots
import freeimagehost
from bots.discord.utils.galleries import create_gallery, GalleryItem, add_video_link
from bots.discord.utils.webhooks import get_channel_send_webhook
from bots.vk.utils import get_photo_max_size, get_video_max_size
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

Attachment = MessagesMessageAttachment | WallWallpostAttachment | WallCommentAttachment


class BaseDiscordMessage(TypedDict):
    content: str
    embeds: list[discord.Embed]
    view: discord.ui.View


class EditDiscordMessage(BaseDiscordMessage):
    pass


class NewDiscordMessage(BaseDiscordMessage):
    avatar_url: str
    username: str




@dataclass
class ProcessedAttachments:
    images: list[GalleryItem] = field(default_factory=list)
    gif_images: list[GalleryItem] = field(default_factory=list)
    videos: list[GalleryItem] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    audios: list[AudioAudio] = field(default_factory=list)
    embed_type: str = EMBED_TYPE_NULL
    embed_args: list[Any] = field(default_factory=list)

    def extend(self, other: "ProcessedAttachments") -> None:
        self.images.extend(other.images)
        self.gif_images.extend(other.gif_images)
        self.audios.extend(other.audios)
        self.videos.extend(other.videos)
        self.files = {**self.files, **other.files}


async def make_basic_embed(vk_message: vkbottle.bot.Message, text=None) -> discord.Embed:
    timestamp = datetime.utcfromtimestamp(vk_message.date)
    if text:
        embed = discord.Embed(description=text, timestamp=timestamp)
    else:
        embed = discord.Embed(timestamp=timestamp)

    return embed


async def process_attachments(attachments: list[Attachment]):
    media = ProcessedAttachments()
    for attachment in attachments:
        if photo := attachment.photo:
            media.embed_type = EMBED_TYPE_BASIC
            photo_size = get_photo_max_size(photo.sizes)
            media.images.append(GalleryItem(image_url=photo_size.url))
        elif doc := attachment.doc:
            media.embed_type = EMBED_TYPE_BASIC
            if doc.type == DOC_IMAGE_TYPE:
                media.images.append(GalleryItem(image_url=doc.url))
            elif doc.type == DOC_GIF_TYPE:
                media.gif_images.append(GalleryItem(image_url=doc.url))
            else:
                media.files[doc.title] = doc.url
        elif audio := attachment.audio:
            media.embed_type = EMBED_TYPE_BASIC
            media.audios.append(audio)
        elif video := attachment.video:
            media.embed_type = EMBED_TYPE_BASIC
            video_url = rf'https://vk.com/video{video.owner_id}_{video.id}'
            video_name = video.title
            image_url = get_video_max_size(video.image).url
            media.videos.append(GalleryItem(image_url=image_url, video_link=video_url, video_name=video_name))
        elif isinstance(attachment, MessagesMessageAttachment):
            if sticker := attachment.sticker:
                media.embed_type = EMBED_TYPE_BASIC
                for size in sticker.images:
                    if size.width == 128:
                        size_128 = size
                        media.images.append(GalleryItem(image_url=size_128.url))
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


async def process_images(images: list[GalleryItem],
                         embed: discord.Embed,
                         buttons: discord.ui.View) -> tuple[list[discord.Embed], discord.ui.View]:
    images_count = len(images)
    if images_count == 0:
        return [embed] if embed else [], buttons
    elif images_count == 1:
        image = images[0]
        embed.set_image(image.image_url)
        add_video_link(embed, image)
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


async def process_files(files, embed: discord.Embed) -> discord.Embed:
    if files:
        docs = '\n'.join([f'[{doc_name}]({doc_url})'
                          for doc_name, doc_url in files.items()])
        embed.add_field(
            name='Документы',
            value=docs,
            inline=False
        )

    return embed


def handle_mention(match: re.Match) -> str:
    groups = match.groups()
    return MENTION_LINK.format(
        text=groups[2],
        id_type=groups[0],
        id_value=groups[1]
    )


async def replace_mentions_as_links(text: str, mention: Mention | None = None) -> str:
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
                      embed: discord.Embed | None,
                      buttons: discord.ui.View) -> tuple[list[discord.Embed], discord.ui.View]:
    uploaded_gif_images = (
        await freeimagehost.multiple_upload_and_get_url(gif.image_url for gif in media.gif_images)
    )
    for gif, uploaded_url in zip(media.gif_images, uploaded_gif_images):
        gif.image_url = uploaded_url

    uploaded_video_images = (
        await freeimagehost.multiple_upload_and_get_url(video.image_url for video in media.videos)
    )
    for video, uploaded_url in zip(media.videos, uploaded_video_images):
        video.image_url = uploaded_url

    media.images = media.videos + media.images + media.gif_images

    embed = await process_files(media.files, embed)
    embed = await process_audios(media.audios, embed)

    if embed:
        embed.description = await replace_mentions_as_links(embed.description)

    embeds, buttons = await process_images(media.images, embed, buttons)

    return embeds, buttons


async def get_discord_message(vk_message: vkbottle.bot.Message,
                              for_edit: bool = False) -> NewDiscordMessage | EditDiscordMessage:
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
        return EditDiscordMessage(
            content=text,
            embeds=embeds,
            view=buttons
        )
    else:
        from_info = await get_from_info(vk_message.from_id)
        await from_info.load_nickname()
        return NewDiscordMessage(
            content=text,
            embeds=embeds,
            view=buttons,
            avatar_url=from_info.avatar_url,
            username=from_info.nickname
        )


async def send_to_discord(channel_id: int, vk_message: vkbottle.bot.Message) -> None:
    try:
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
    except Exception:
        traceback.print_exc()

