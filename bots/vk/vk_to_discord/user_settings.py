import vkbottle.bot
import db_helpers
from vkbottle.bot import Blueprint

bp = Blueprint('vk_to_discord_user_settings')


@bp.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/nickname')))
async def set_nickname(message: vkbottle.bot.Message):
    nickname = message.text.replace('/nickname ', '')
    user = await message.get_user()
    await db_helpers.set_vk_nickname(user.id, nickname)
    await message.answer(f'Никнейм {nickname} успешно установлен')


@bp.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/removenickname')))
async def remove_nickname(message: vkbottle.bot.Message):
    user = await message.get_user()
    await db_helpers.set_vk_nickname(user.id, None)
    await message.answer(f'Никнейм успешно удален')
