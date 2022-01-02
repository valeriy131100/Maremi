import vkbottle.bot
import db_helpers
from vkbottle.bot import Blueprint
from bots.vk.custom_rules import StartsWithRule
from models import VkNickName

bp = Blueprint('vk_to_discord_user_settings')


@bp.on.chat_message(StartsWithRule('nickname'))
async def set_nickname(message: vkbottle.bot.Message, cleared_text):
    nickname = cleared_text
    await VkNickName.update_or_create(
        vk_id=message.from_id,
        defaults={
            'nickname': nickname
        }
    )
    await message.answer(f'Никнейм {nickname} успешно установлен')


@bp.on.chat_message(StartsWithRule('removenickname', return_text=False))
async def remove_nickname(message: vkbottle.bot.Message):
    await VkNickName.update_or_create(
        vk_id=message.from_id,
        defaults={
            'nickname': ''
        }
    )
    await message.answer(f'Никнейм успешно удален')
