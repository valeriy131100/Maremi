import vkbottle.bot
import db_helpers
from vkbottle.bot import Blueprint
from bots.vk.custom_rules import StartsWithRule

bp = Blueprint('vk_to_discord_user_settings')


@bp.on.chat_message(StartsWithRule('nickname'))
async def set_nickname(message: vkbottle.bot.Message, cleared_text):
    nickname = cleared_text
    user = await message.get_user()
    await db_helpers.set_vk_nickname(user.id, nickname)
    await message.answer(f'Никнейм {nickname} успешно установлен')


@bp.on.chat_message(StartsWithRule('removenickname', return_text=False))
async def remove_nickname(message: vkbottle.bot.Message):
    user = await message.get_user()
    await db_helpers.set_vk_nickname(user.id, None)
    await message.answer(f'Никнейм успешно удален')
