import discord
import vkbottle.bot
from discord.ext import commands
from aiosqlite import IntegrityError
from pathlib import Path
from vkbottle_types.objects import PhotosPhotoSizesType

import asyncio
from config import vk_token, discord_token, db_file
import db_helpers
from vk_utils import get_random_id, get_user_photo

vk_bot = vkbottle.bot.Bot(vk_token)
discord_bot = commands.Bot(command_prefix='m.')


temp = {
    'chats': {
        # dict vk_chat_id: on/off bool
    }
}


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message, text_replace=None, embed=True):
    channel = discord_bot.get_channel(id=channel_id)
    text = vk_message.text
    if text_replace:
        for s, s_replace in text_replace.items():
            text = text.replace(s, s_replace)
            if not text:
                break
    if text:
        if embed:
            user = await vk_message.get_user(fields=['photo_50'])
            embed_message = discord.Embed(description=vk_message.text)
            embed_message.set_author(
                name=f'{user.first_name} {user.last_name}',
                icon_url=f'{user.photo_50}'
            )
            if vk_message.attachments:
                for attachment in vk_message.attachments:
                    if photo := attachment.photo:
                        for size in photo.sizes:
                            if size.type == PhotosPhotoSizesType.Z:
                                embed_message.set_image(url=size.url)
                        break
            await channel.send(embed=embed_message)
            return
        else:
            await channel.send(text)

    if vk_message.attachments:
        for attachment in vk_message.attachments:
            if photo := attachment.photo:
                for size in photo.sizes:
                    if size.type == PhotosPhotoSizesType.Z:
                        await channel.send(size.url)


async def send_to_vk(chat_id, discord_message: discord.Message):
    await vk_bot.api.messages.send(chat_id=chat_id, message=discord_message.content, random_id=get_random_id())


@discord_bot.event
async def on_message(message: discord.Message):
    if await db_helpers.is_duplex_channel(message.guild.id, message.channel.id):
        if not (message.content.startswith('m.') or message.author == discord_bot.user):
            chat_id = await db_helpers.get_server_chat(message.guild.id)
            await send_to_vk(chat_id, message)


@discord_bot.command()
async def start(context: commands.Context):
    await context.send(f'Привет! channel_id={context.channel.id}')


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


@discord_bot.command()
async def alias(context: commands.Context, alias_word):
    try:
        await db_helpers.make_alias(context.guild.id, context.channel.id, alias_word)
        await context.send(f'Алиас {alias_word} для канала был создан. Используйте #{alias_word} в вк-боте, '
                           f'чтобы слать сюда сообщения.')
    except IntegrityError:
        await context.send(f'Подобный алиас уже существует. Используйте {context.prefix}removealias')


@discord_bot.command()
async def removealias(context: commands.Context, alias_word):
    try:
        await db_helpers.delete_alias(context.guild.id, alias_word)
    except IndexError:
        await context.send(f'Алиас не найден')
    else:
        await context.send(f'Алиас {alias_word} успешно удален')


@discord_bot.command()
async def setdefault(context: commands.Context):
    await db_helpers.set_default_channel(server_id=context.guild.id, channel_id=context.channel.id)
    await context.send(f'Текущий канал установлен как канал по умолчанию')


@discord_bot.command()
async def setart(context: commands.Context):
    await db_helpers.set_default_image_channel(server_id=context.guild.id, channel_id=context.channel.id)
    await context.send(f'Текущий канал установлен как канал по умолчанию для изображений')


@discord_bot.command()
async def setduplex(context: commands.Context):
    await db_helpers.set_duplex_channel(server_id=context.guild.id, channel_id=context.channel.id)
    await context.send(f'Текущий канал установлен как дуплексный канал')


@vk_bot.on.chat_message(text='/start')
async def start(message: vkbottle.bot.Message):
    await message.answer(f'Привет. chat_id={message.chat_id}')


@vk_bot.on.chat_message(text='/makeonline')
async def make_online(message: vkbottle.bot.Message):
    temp['chats'][message.chat_id] = True
    await message.answer(f'К чату теперь можно подключиться. Напишите дискорд-боту m.connect {message.chat_id}')


@vk_bot.on.chat_message(text='/makeoffline')
async def make_online(message: vkbottle.bot.Message):
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
            text = message.text.replace(f'#{alias}', '')
            channel_id = await db_helpers.get_channel_by_alias(alias, chat_id=message.chat_id)
            await send_to_discord(channel_id, message, {f'#{alias} ': '', f'#{alias}': ''})
            return

    await message.answer(f'Не удалось найти алиас')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: not message.text.startswith(('/', '#'))))
async def duplex_chat(message: vkbottle.bot.Message):
    duplex_channel = await db_helpers.get_chat_duplex_channel(message.chat_id)
    print(duplex_channel)
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

