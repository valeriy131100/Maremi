import disnake as discord
import vkbottle.bot
import bots
import db_helpers
from datetime import datetime

from bots.discord.utils.galleries import create_gallery
from bots.vk.utils import get_photo_max_size


async def make_embed(vk_message: vkbottle.bot.Message, text=None):
    timestamp = datetime.utcfromtimestamp(vk_message.date)
    if text:
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

        images_count = len(images)
        if images_count == 1:
            embed_message = await make_embed(vk_message)
            embed_message.set_image(images[0])
            await webhook.send(
                text,
                embed=embed_message,
                avatar_url=avatar_url,
                username=username,
            )
        elif images_count > 1:
            embed_message = await make_embed(vk_message, text)
            embed_message, buttons = await create_gallery(
                images,
                embed=embed_message,
                upload=False
            )
            await webhook.send(
                embed=embed_message,
                avatar_url=avatar_url,
                username=username,
                view=buttons
            )
        elif text:
            await webhook.send(text, avatar_url=avatar_url, username=username)
    else:
        await webhook.send(text, avatar_url=avatar_url, username=username)

    await webhook.delete()

