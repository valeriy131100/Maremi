import vkbottle.bot
from vkbottle_types.events import GroupEventType
import bots
import config
import db_helpers
from . import converter
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
    await converter.send_to_discord(channel_id, message)


@bp.on.chat_message(StartsWithRule('art'))
async def send_art(message: vkbottle.bot.Message, cleared_text):
    channel_id = await db_helpers.get_default_image_channel(
        chat_id=message.chat_id
    )
    message.text = cleared_text
    await converter.send_to_discord(channel_id, message)


@bp.on.chat_message(AliasRule())
async def alias_send(message: vkbottle.bot.Message, cleared_text, alias):
    channel_id = await db_helpers.get_channel_by_alias(
        alias, chat_id=message.chat_id
    )
    message.text = cleared_text
    await converter.send_to_discord(channel_id, message)
    return


@bp.on.chat_message(NotStartsWithRule())
async def duplex_chat(message: vkbottle.bot.Message):
    duplex_channel = await db_helpers.get_chat_duplex_channel(message.chat_id)
    if duplex_channel:
        await converter.send_to_discord(duplex_channel, message)


@bp.on.raw_event(event=GroupEventType.MESSAGE_EDIT,
                 dataclass=vkbottle.bot.MessageEvent)
async def duplex_edit(event: vkbottle.bot.MessageEvent):
    if event.group_id == config.vk_group_id:
        return
    discord_message_raw = await db_helpers.get_discord_message(event)
    if not discord_message_raw:
        return

    vk_messages = await bots.vk_bot.api.messages.get_by_conversation_message_id(
        peer_id=event.peer_id,
        conversation_message_ids=[event.conversation_message_id]
    )
    vk_message = vk_messages.items[0]

    channel_id, discord_message_id = discord_message_raw
    channel = bots.discord_bot.get_channel(channel_id)
    discord_message = await channel.fetch_message(discord_message_id)
    discord_message.edit(
        **(await converter.get_discord_message(vk_message))
    )

