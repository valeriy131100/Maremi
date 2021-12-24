from datetime import datetime

import aiofiles
import disnake as discord
import vkbottle.bot
import bots
import db_helpers
from config import vk_token
from vk_utils import get_photo_max_size

vk_bot = vkbottle.bot.Bot(vk_token)


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
        first_embed = True
        for attachment in vk_message.attachments:
            if photo := attachment.photo:
                photo_size = get_photo_max_size(photo.sizes)
                if first_embed:
                    embed_message = await make_embed(vk_message)
                    embed_message.set_image(url=photo_size.url)
                    first_embed = False
                    await webhook.send(
                        text,
                        embed=embed_message,
                        avatar_url=avatar_url,
                        username=username
                    )
                else:
                    photo_embed = await make_embed(vk_message)
                    photo_embed.set_image(url=photo_size.url)
                    await webhook.send(
                        embed=photo_embed,
                        avatar_url=avatar_url,
                        username=username
                    )
            elif sticker := attachment.sticker:
                for size in sticker.images:
                    if size.width == 128:
                        size_128 = size
                embed_message = await make_embed(vk_message, text)
                embed_message.set_image(url=size_128.url)
                await webhook.send(embed=embed_message, avatar_url=avatar_url, username=username)
                return
    else:
        await webhook.send(text, avatar_url=avatar_url, username=username)

    await webhook.delete()


@vk_bot.on.chat_message(text='/start')
async def start(message: vkbottle.bot.Message):
    await message.answer(f'Привет. chat_id={message.chat_id}')


@vk_bot.on.chat_message(text='/help')
async def help_(message: vkbottle.bot.Message):
    async with aiofiles.open('vk_help_message.txt', mode='r', encoding='utf-8') as help_file:
        help_text = await help_file.read()
        await message.answer(help_text)


@vk_bot.on.chat_message(text='/makeonline')
async def make_online(message: vkbottle.bot.Message):
    bots.temp['chats'][message.chat_id] = True
    await message.answer(f'К чату теперь можно подключиться. Напишите дискорд-боту m.connect {message.chat_id}')


@vk_bot.on.chat_message(text='/makeoffline')
async def make_offline(message: vkbottle.bot.Message):
    bots.temp['chats'][message.chat_id] = False
    await message.answer(f'К чату теперь нельзя подключиться')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/send')))
async def send(message: vkbottle.bot.Message):
    channel_id = await db_helpers.get_default_channel(chat_id=message.chat_id)
    await send_to_discord(channel_id, message, text_replace={'/send ': '', '/send': ''})


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/art')))
async def send_art(message: vkbottle.bot.Message):
    channel_id = await db_helpers.get_default_image_channel(chat_id=message.chat_id)
    await send_to_discord(channel_id, message, text_replace={'/art ': '', '/art': ''})


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('#')))
async def alias_send(message: vkbottle.bot.Message):
    aliases = await db_helpers.get_aliases(chat_id=message.chat_id)
    for alias in aliases:
        if message.text.startswith(f'#{alias}'):
            channel_id = await db_helpers.get_channel_by_alias(alias, chat_id=message.chat_id)
            await send_to_discord(channel_id, message, {f'#{alias} ': '', f'#{alias}': ''})
            return

    await message.answer(f'Не удалось найти алиас')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/nickname')))
async def set_nickname(message: vkbottle.bot.Message):
    nickname = message.text.replace('/nickname ', '')
    user = await message.get_user()
    await db_helpers.set_vk_nickname(user.id, nickname)
    await message.answer(f'Никнейм {nickname} успешно установлен')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/removenickname')))
async def remove_nickname(message: vkbottle.bot.Message):
    user = await message.get_user()
    await db_helpers.set_vk_nickname(user.id, None)
    await message.answer(f'Никнейм успешно удален')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: not message.text.startswith(('/', '#'))))
async def duplex_chat(message: vkbottle.bot.Message):
    duplex_channel = await db_helpers.get_chat_duplex_channel(message.chat_id)
    if duplex_channel:
        await send_to_discord(duplex_channel, message)
        