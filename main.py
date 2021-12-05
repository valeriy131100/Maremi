from pathlib import Path

import vkbottle.bot
from discord.ext import commands
from aiosqlite import IntegrityError

import asyncio
from config import vk_token, discord_token, db_file
import db_helpers

vk_bot = vkbottle.bot.Bot(vk_token)
discord_bot = commands.Bot(command_prefix='m.')


temp = {
    'chats': {
        # dict vk_chat_id: on/off bool
    }
}


async def send_to_discord(channel_id, vk_message: vkbottle.bot.Message):
    channel = discord_bot.get_channel(id=channel_id)
    if vk_message.text:
        await channel.send(vk_message.text)


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
    text = message.text.replace('/send ', '')
    channel_id = await db_helpers.get_default_channel(chat_id=message.chat_id)
    await send_to_discord(channel_id, message)


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('#')))
async def send(message: vkbottle.bot.Message):
    aliases = await db_helpers.get_aliases(chat_id=message.chat_id)
    for alias in aliases:
        if message.text.startswith(f'#{alias}'):
            text = message.text.replace(f'#{alias}', '')
            channel_id = await db_helpers.get_channel_by_alias(alias, chat_id=message.chat_id)
            await send_to_discord(channel_id, message)
            return

    await message.answer(f'Не удалось найти алиас')

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

