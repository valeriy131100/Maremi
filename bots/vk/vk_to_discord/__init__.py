import vkbottle.bot
import db_helpers
from .converter import send_to_discord
from vkbottle.bot import Blueprint
from .connect import bp as connect_bp
from .user_settings import bp as user_bp

bp = Blueprint('send_to_discord')
bp.child_bps = [connect_bp, user_bp]


@bp.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/send')))
async def send(message: vkbottle.bot.Message):
    channel_id = await db_helpers.get_default_channel(chat_id=message.chat_id)
    await send_to_discord(channel_id, message, text_replace={'/send ': '', '/send': ''})


@bp.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('/art')))
async def send_art(message: vkbottle.bot.Message):
    channel_id = await db_helpers.get_default_image_channel(chat_id=message.chat_id)
    await send_to_discord(channel_id, message, text_replace={'/art ': '', '/art': ''})


@bp.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: message.text.startswith('#')))
async def alias_send(message: vkbottle.bot.Message):
    aliases = await db_helpers.get_aliases(chat_id=message.chat_id)
    for alias in aliases:
        if message.text.startswith(f'#{alias}'):
            channel_id = await db_helpers.get_channel_by_alias(alias, chat_id=message.chat_id)
            await send_to_discord(channel_id, message, {f'#{alias} ': '', f'#{alias}': ''})
            return

    await message.answer(f'Не удалось найти алиас')


@bp.on.chat_message(vkbottle.bot.rules.FuncRule(lambda message: not message.text.startswith(('/', '#'))))
async def duplex_chat(message: vkbottle.bot.Message):
    duplex_channel = await db_helpers.get_chat_duplex_channel(message.chat_id)
    if duplex_channel:
        await send_to_discord(duplex_channel, message)
