import time

import disnake as discord
import vkbottle.bot
import aiofiles
from disnake.ext import commands
from aiosqlite import IntegrityError
from pathlib import Path
from vkbottle import PhotoMessageUploader
from discord_utils import EMOJI_REGEX, download_emoji, download_file

import asyncio
import os
from datetime import datetime
from config import vk_token, discord_token, db_file
import db_helpers
import freeimagehost
from vk_utils import get_random_id, get_photo_max_size

vk_bot = vkbottle.bot.Bot(vk_token)
discord_bot = commands.Bot(command_prefix='m.', help_command=None)


temp = {
    'chats': {
        # dict vk_chat_id: on/off bool
    },
    'webhooks': [
        # webhooks_ids
    ],
}


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
    channel = discord_bot.get_channel(channel_id)
    text = vk_message.text
    if text_replace:
        for s, s_replace in text_replace.items():
            text = text.replace(s, s_replace)
            if not text:
                break

    username, avatar_url = await get_user_info_from_vk_message(vk_message)
    webhook = await channel.create_webhook(name=username)
    temp['webhooks'].append(webhook.id)

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


async def send_to_vk(chat_id, discord_message: discord.Message):
    nickname = await db_helpers.get_discord_nickname(discord_message.author.id)
    message_text = discord_message.content
    photo_uploader = PhotoMessageUploader(api=vk_bot.api)
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

    await vk_bot.api.messages.send(chat_id=chat_id, message=message_text, random_id=get_random_id(),
                                   attachment=attachments)


@discord_bot.event
async def on_message(message: discord.Message):
    if ((await db_helpers.is_duplex_channel(message.guild.id, message.channel.id))
            and not message.author == discord_bot.user
            and not message.content.startswith(discord_bot.command_prefix)
            and message.webhook_id not in temp['webhooks']):
        chat_id = await db_helpers.get_server_chat(message.guild.id)
        await send_to_vk(chat_id, message)
    else:
        await discord_bot.process_commands(message)


@discord_bot.listen()
async def on_button_click(interaction):
    if interaction.component.custom_id.startswith('gallery'):
        await handle_gallery_button(interaction)


@discord_bot.command(name='help')
async def help_(context: commands.Context):
    async with aiofiles.open('discord_help_message.txt', mode='r', encoding='utf-8') as help_file:
        help_text = await help_file.read()
        await context.send(help_text)


@discord_bot.command()
async def start(context: commands.Context):
    await context.send(f'Привет! channel_id={context.channel.id}')


@discord_bot.command()
async def split(context: commands.Context):
    if ref := context.message.reference:
        ref_message = await context.channel.fetch_message(ref.message_id)
        if attaches := ref_message.attachments:
            author_name = ref_message.author.display_name
            author_avatar = ref_message.author.avatar.url
            webhook = await context.channel.create_webhook(name=author_name)
            temp['webhooks'].append(webhook.id)
            first_embed = True
            for attach in attaches:
                timestamp = ref_message.created_at
                embed = discord.Embed(timestamp=timestamp)
                embed.set_image(url=attach.url)
                if first_embed:
                    await webhook.send(
                        ref_message.content,
                        embed=embed,
                        username=author_name,
                        avatar_url=author_avatar
                    )
                    first_embed = False
                else:
                    await webhook.send(
                        embed=embed,
                        username=author_name,
                        avatar_url=author_avatar
                    )
            await webhook.delete()
            await ref_message.delete()
            await context.message.delete()
        else:
            await context.send('Оригинальное сообщение не содержит изображений')
    else:
        await context.send('Пожалуйста, ответьте на сообщение, которое хотите разделить')


@discord_bot.group(pass_context=True)
async def make(context: commands.Context):
    pass


@make.command(name='alias')
async def set_alias(context: commands.Context, alias_word):
    try:
        await db_helpers.make_alias(context.guild.id, context.channel.id, alias_word)
        await context.send(f'Алиас {alias_word} для канала был создан. Используйте #{alias_word} в вк-боте, '
                           f'чтобы слать сюда сообщения.')
    except IntegrityError:
        await context.send(f'Подобный алиас уже существует. Используйте {context.prefix}removealias')


@make.command(name='gallery')
async def make_gallery(context: commands.Context):
    original_message = None
    if ref := context.message.reference:
        message = await context.channel.fetch_message(ref.message_id)
        original_message = context.message
    else:
        message = context.message
    images_count = len(message.attachments)
    gallery_images = []
    gallery_message = await context.send(f'Загружаю {images_count} изображений')
    for image_num, attachment in enumerate(message.attachments):
        image = await freeimagehost.upload_and_get_url(attachment.url)
        if image:
            gallery_images.append(image)
            await gallery_message.edit(content=f'Загружаю картинку {image_num+1} из {images_count}')
    gallery_id = await db_helpers.create_gallery(gallery_images)
    embed, buttons = await get_gallery_message(0, gallery_id)
    await message.delete()
    if original_message:
        await original_message.delete()
    await gallery_message.edit(content='', embed=embed, view=buttons)


async def get_gallery_message(attachment_id, gallery_id):
    attachments = await db_helpers.get_gallery_images(gallery_id)
    buttons = discord.ui.View()
    buttons.add_item(
        discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Назад",
            custom_id=f"gallery prev {attachment_id} {gallery_id}"
        )
    )
    buttons.add_item(
        discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Вперёд",
            custom_id=f"gallery next {attachment_id} {gallery_id}"
        )
    )

    embed = discord.Embed()
    embed.set_image(url=attachments[attachment_id])

    return embed, buttons


async def handle_gallery_button(interaction: discord.MessageInteraction):
    payload = interaction.component.custom_id
    _, command, attachment_id, gallery_id = payload.split()
    attachment_id = int(attachment_id)
    gallery_id = int(gallery_id)
    attachments = await db_helpers.get_gallery_images(gallery_id)

    if command == 'next':
        if attachment_id == len(attachments) - 1:
            attachment_id = 0
        else:
            attachment_id += 1
    elif command == 'prev':
        if attachment_id == 0:
            attachment_id = len(attachments) - 1
        else:
            attachment_id -= 1

    embed, buttons = await get_gallery_message(attachment_id, gallery_id)
    await interaction.response.edit_message(embed=embed, view=buttons)


@discord_bot.group(pass_context=True, name='set')
async def set_(context: commands.Context):
    pass


@set_.command(name='nickname')
async def set_nickname(context: commands.Context, nickname):
    await db_helpers.set_discord_nickname(context.author.id, nickname)
    await context.send(f'Никнейм {nickname} успешно установлен')


@set_.command(name='default')
async def set_default(context: commands.Context):
    await db_helpers.set_default_channel(server_id=context.guild.id, channel_id=context.channel.id)
    await context.send(f'Текущий канал установлен как канал по умолчанию')


@set_.command(name='art')
async def set_art(context: commands.Context):
    await db_helpers.set_default_image_channel(server_id=context.guild.id, channel_id=context.channel.id)
    await context.send(f'Текущий канал установлен как канал по умолчанию для изображений')


@set_.command(name='duplex')
async def set_duplex(context: commands.Context):
    await db_helpers.set_duplex_channel(server_id=context.guild.id, channel_id=context.channel.id)
    await context.send(f'Текущий канал установлен как дуплексный канал')


@discord_bot.group(pass_context=True, name='remove')
async def remove(context: commands.Context):
    pass


@remove.command(name='nickname')
async def remove_nickname(context: commands.Context):
    await db_helpers.set_discord_nickname(context.author.id, None)
    await context.send(f'Никнейм успешно удален')


@remove.command(name='alias')
async def remove_alias(context: commands.Context, alias_word):
    try:
        await db_helpers.delete_alias(context.guild.id, alias_word)
    except IndexError:
        await context.send(f'Алиас не найден')
    else:
        await context.send(f'Алиас {alias_word} успешно удален')


@discord_bot.command()
async def connect(context: commands.Context, chat_id):
    try:
        chat_id = int(chat_id)
    except ValueError:
        await context.send(f'Это не id чата Вконтакте')
    else:
        if temp['chats'].get(chat_id, False):
            await db_helpers.make_server_to_chat(context.guild.id, chat_id, default_channel=context.channel.id)
            await context.send(f'Сервер {context.guild.id} успешно привязан к чату {chat_id}')
            await context.send(f'Канал по умолчанию установлен на текущий ({context.channel.id})')
        else:
            await context.channel.send(f'Чат {chat_id} не разрешил себя привязывать')


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
    temp['chats'][message.chat_id] = True
    await message.answer(f'К чату теперь можно подключиться. Напишите дискорд-боту m.connect {message.chat_id}')


@vk_bot.on.chat_message(text='/makeoffline')
async def make_offline(message: vkbottle.bot.Message):
    temp['chats'][message.chat_id] = False
    await message.answer(f'К чату теперь нельзя подключиться')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/send')))
async def send(message: vkbottle.bot.Message):
    channel_id = await db_helpers.get_default_channel(chat_id=message.chat_id)
    await send_to_discord(channel_id, message, text_replace={'/send ': '', '/send': ''})


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/art')))
async def send(message: vkbottle.bot.Message):
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


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    if not Path(db_file).is_file():
        loop.run_until_complete(db_helpers.create_db())

    loop.run_until_complete(
        asyncio.gather(
            discord_bot.start(discord_token),
            vk_bot.run_polling()
        )
    )
