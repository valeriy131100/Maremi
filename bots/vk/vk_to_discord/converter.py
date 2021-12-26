from typing import Optional

import disnake as discord
import vkbottle.bot
import bots
import db_helpers
from datetime import datetime
from vkbottle_types.objects import WallWallpostFull

from bots.discord.utils.galleries import create_gallery
from bots.vk.utils import get_photo_max_size


POST_URL_TEMPLATE = 'https://vk.com/wall{from_id}_{post_id}'
FROM_USER_TEMPLATE = 'https://vk.com/id{from_id}'
FROM_GROUP_TEMPLATE = 'https://vk.com/club{from_id}'


async def make_embed(vk_message: vkbottle.bot.Message, text=None,
                     post: Optional[WallWallpostFull] = None):
    timestamp = datetime.utcfromtimestamp(vk_message.date)
    if post:
        post_text = post.text
        if post_text and len(post_text) > 4096:
            post_text = f'{post.text[:4093]}...'

        post_link = POST_URL_TEMPLATE.format(
            from_id=post.from_id,
            post_id=post.id
        )

        post_timestamp = datetime.utcfromtimestamp(post.date)

        embed_message = discord.Embed(
            title=f'Запись на стене',
            url=post_link,
            description=post_text,
            timestamp=post_timestamp
        )

        from_name, from_avatar, from_url = (
            await get_from_info_from_wall_post(post)
        )

        embed_message.set_author(
            name=from_name,
            icon_url=from_avatar,
            url=from_url
        )

        embed_message.add_field(
            name='❤️',
            value=post.likes.count
        )
        embed_message.add_field(
            name='💬',
            value=post.comments.count
        )
    elif text:
        embed_message = discord.Embed(description=text, timestamp=timestamp)
    else:
        embed_message = discord.Embed(timestamp=timestamp)

    return embed_message


async def get_user_info_from_vk_message(vk_message: vkbottle.bot.Message):
    user = await vk_message.get_user(fields=['photo_50'])
    user_nickname = await db_helpers.get_vk_nickname(user.id)
    if user_nickname:
        username = f'{user_nickname} ({user.first_name} {user.last_name})'
    else:
        username = f'{user.first_name} {user.last_name}'

    avatar_url = f'{user.photo_50}'

    return username, avatar_url


async def get_from_info_from_wall_post(post: WallWallpostFull):
    from_id = post.from_id
    if from_id < 0:
        group_info = await bots.vk_bot.api.groups.get_by_id(
            group_id=str(abs(from_id))
        )
        group_name = group_info[0].name
        group_avatar = group_info[0].photo_200
        group_url = FROM_GROUP_TEMPLATE.format(from_id=abs(post.from_id))
        return group_name, group_avatar, group_url
    else:
        user_info = await bots.vk_bot.api.users.get(
            user_ids=[from_id], fields=['photo_200']
        )
        user_name = f'{user_info[0].first_name} {user_info[0].last_name}'
        user_avatar = user_info[0].photo_200
        user_url = FROM_USER_TEMPLATE.format(from_id=post.from_id)
        return user_name, user_avatar, user_url


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message, text_replace=None):
    channel = bots.discord_bot.get_channel(channel_id)
    text = vk_message.text
    if text_replace:
        for s, s_replace in text_replace.items():
            text = text.replace(s, s_replace)
            if not text:
                break

    username, avatar_url = await get_user_info_from_vk_message(vk_message)
    webhook = await channel.create_webhook(name=username)
    bots.temp['webhooks'].append(webhook.id)

    if vk_message.attachments:
        images = []
        post_to_send = None
        for attachment in vk_message.attachments:
            if photo := attachment.photo:
                photo_size = get_photo_max_size(photo.sizes)
                images.append(photo_size.url)
            elif sticker := attachment.sticker:
                for size in sticker.images:
                    if size.width == 128:
                        size_128 = size
                        embed_message = await make_embed(vk_message)
                        embed_message.set_image(url=size_128.url)
                        await webhook.send(
                            embed=embed_message,
                            avatar_url=avatar_url,
                            username=username
                        )
            elif post := attachment.wall:
                post_to_send = post
                if post.attachments:
                    for post_attachment in post.attachments:
                        if post_photo := post_attachment.photo:
                            photo_size = get_photo_max_size(post_photo.sizes)
                            images.append(photo_size.url)

        images_count = len(images)
        embed_message = await make_embed(
            vk_message,
            post=post_to_send
        )
        if images_count == 1:
            embed_message.set_image(images[0])
            await webhook.send(
                text,
                embed=embed_message,
                avatar_url=avatar_url,
                username=username,
            )
        elif images_count > 1:
            embed_message, buttons = await create_gallery(
                images,
                embed=embed_message,
                upload=False
            )
            await webhook.send(
                text,
                embed=embed_message,
                avatar_url=avatar_url,
                username=username,
                view=buttons
            )
        elif post_to_send:
            # post without images
            await webhook.send(
                embed=embed_message,
                avatar_url=avatar_url,
                username=username
            )
        elif text:
            await webhook.send(
                text,
                avatar_url=avatar_url,
                username=username
            )
    else:
        await webhook.send(text, avatar_url=avatar_url, username=username)

    await webhook.delete()

