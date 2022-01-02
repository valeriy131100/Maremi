import vkbottle.bot
from vkbottle_types.events import GroupEventType
import bots
import config
from . import converter
from vkbottle.bot import Blueprint
from .connect import bp as connect_bp
from .user_settings import bp as user_bp
from bots.vk.custom_rules import StartsWithRule, AliasRule, NotStartsWithRule
from models import Server, ServerChannelAlias

bp = Blueprint('send_to_discord')
bp.child_bps = [connect_bp, user_bp]


@bp.on.chat_message(StartsWithRule('send'))
async def send(message: vkbottle.bot.Message, cleared_text):
    server = await Server.get(chat_id=message.chat_id)
    channel_id = server.server_default_channel
    message.text = cleared_text
    await converter.send_to_discord(channel_id, message)


@bp.on.chat_message(StartsWithRule('art'))
async def send_art(message: vkbottle.bot.Message, cleared_text):
    server = await Server.get(chat_id=message.chat_id)
    channel_id = server.default_image_channel
    message.text = cleared_text
    await converter.send_to_discord(channel_id, message)


@bp.on.chat_message(AliasRule())
async def alias_send(message: vkbottle.bot.Message, cleared_text, alias):
    server = await Server.get(chat_id=message.chat_id)
    server_alias = await ServerChannelAlias.get(
        server=server,
        alias=alias
    )
    message.text = cleared_text
    await converter.send_to_discord(server_alias.channel_id, message)
    return


@bp.on.chat_message(NotStartsWithRule())
async def duplex_chat(message: vkbottle.bot.Message):
    server = await Server.get(chat_id=message.chat_id)
    if duplex_channel := server.duplex_channel:
        await converter.send_to_discord(duplex_channel, message)
        
        
def event_to_message(event: dict):
    message = event['object']
    event['object'] = None
    event['object'] = {
        'message': message,
        'client_info': {}
    }
    message = vkbottle.tools.dev.mini_types.bot.message_min(
        event,
        ctx_api=bots.vk_bot.api
    )

    return message

