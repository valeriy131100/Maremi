import discord
from discord.ext import commands
import vkbottle.bot

import asyncio
from config import vk_token, discord_token

vk_bot = vkbottle.bot.Bot(vk_token)
discord_bot = commands.Bot(command_prefix='m.')


temp = {
    'chats': {
        # dict vk_chat_id: on/off bool
    },
    'channels': {
        # dict vk_chat_id: discord_channel_id
    }
}


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
            temp['channels'][chat_id] = context.channel.id
            await context.send(f'Канал {context.channel.id} успешно привязан к чату {chat_id}')
        else:
            await context.channel.send(f'Чат {chat_id} не разрешил себя привязывать')


@vk_bot.on.chat_message(text='/start')
async def start(message: vkbottle.bot.Message):
    await message.answer(f'Привет. chat_id={message.chat_id}')


@vk_bot.on.chat_message(text='/makeonline')
async def make_online(message: vkbottle.bot.Message):
    temp['chats'][message.chat_id] = True
    await message.answer(f'К чату теперь можно подключиться. Напишите дискорд-боту m.connect {message.chat_id}')


@vk_bot.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/send')))
async def send(message: vkbottle.bot.Message):
    text = message.text[message.text.find('/send '):]
    channel_id = temp['channels'][message.chat_id]
    await message.answer(f'Пытаюсь отправить сообщение в канал {channel_id}')
    channel = discord_bot.get_channel(id=channel_id)
    await channel.send(text)


loop = asyncio.get_event_loop()
loop.run_until_complete(
    asyncio.gather(
        discord_bot.start(discord_token),
        vk_bot.run_polling()
    )
)
