import disnake as discord
import vkbottle.bot
import bots
import db_helpers
from datetime import datetime
from bots.discord.utils.galleries import create_gallery
from bots.vk.utils import get_photo_max_size
from .wallpost import make_post_embed


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


async def process_vk_attachments(vk_message: vkbottle.bot.Message):
    images = []
    embed = None
    if vk_message.attachments:

        for attachment in vk_message.attachments:
            if photo := attachment.photo:
                if not embed:
                    embed = await make_basic_embed(vk_message)
                photo_size = get_photo_max_size(photo.sizes)
                images.append(photo_size.url)
            elif sticker := attachment.sticker:
                for size in sticker.images:
                    if size.width == 128:
                        size_128 = size
                        embed = await make_basic_embed(vk_message)
                        images.append(size_128.url)
                break  # sticker always unique
            elif post := attachment.wall:
                embed = await make_post_embed(post)
                if post.attachments:
                    for post_attachment in post.attachments:
                        if post_photo := post_attachment.photo:
                            photo_size = get_photo_max_size(post_photo.sizes)
                            images.append(photo_size.url)

    return await process_images(images, embed)


async def process_images(images, embed):
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


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message,
                          text_replace=None):
    channel = bots.discord_bot.get_channel(channel_id)
    text = vk_message.text
    if text_replace:
        for s, s_replace in text_replace.items():
            text = text.replace(s, s_replace)
            if not text:
                break

    username, avatar_url = await get_user_info_from_vk_message(vk_message)
    embed, buttons = await process_vk_attachments(vk_message)

    webhook = None
    try:
        webhook = await channel.create_webhook(name=username)
        bots.temp['webhooks'].append(webhook.id)

        await webhook.send(
            text,
            embed=embed,
            avatar_url=avatar_url,
            username=username,
            view=buttons
        )
    finally:
        if webhook:
            await webhook.delete()

