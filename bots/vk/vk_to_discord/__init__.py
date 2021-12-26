import vkbottle.bot
import db_helpers
from .converter import send_to_discord
from vkbottle.bot import Blueprint
from .connect import bp as connect_bp
from .user_settings import bp as user_bp
from bots.vk.custom_rules import StartsWithRule, AliasRule, NotStartsWithRule

bp = Blueprint('send_to_discord')
bp.child_bps = [connect_bp, user_bp]


@bp.on.chat_message(StartsWithRule('send'))
async def send(message: vkbottle.bot.Message, cleared_text):
    channel_id = await db_helpers.get_default_channel(chat_id=message.chat_id)
    message.text = cleared_text
    await send_to_discord(channel_id, message)


@bp.on.chat_message(StartsWithRule('art'))
async def send_art(message: vkbottle.bot.Message, cleared_text):
    channel_id = await db_helpers.get_default_image_channel(
        chat_id=message.chat_id
    )
    message.text = cleared_text
    await send_to_discord(channel_id)


@bp.on.chat_message(AliasRule())
async def alias_send(message: vkbottle.bot.Message, cleared_text, alias):
    channel_id = await db_helpers.get_channel_by_alias(
        alias, chat_id=message.chat_id
    )
    message.text = cleared_text
    await send_to_discord(channel_id, message)
    return


@bp.on.chat_message(NotStartsWithRule())
async def duplex_chat(message: vkbottle.bot.Message):
    duplex_channel = await db_helpers.get_chat_duplex_channel(message.chat_id)
    if duplex_channel:
        await send_to_discord(duplex_channel, message)
