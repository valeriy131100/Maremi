import vkbottle
import bots
from vkbottle.bot import Blueprint

bp = Blueprint('vk_to_discord_connect')


@bp.on.chat_message(text='/makeonline')
async def make_online(message: vkbottle.bot.Message):
    bots.temp['chats'][message.chat_id] = True
    await message.answer(f'К чату теперь можно подключиться. Напишите дискорд-боту m.connect {message.chat_id}')


@bp.on.chat_message(text='/makeoffline')
async def make_offline(message: vkbottle.bot.Message):
    bots.temp['chats'][message.chat_id] = False
    await message.answer(f'К чату теперь нельзя подключиться')
