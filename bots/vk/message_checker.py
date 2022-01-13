import asyncio
import traceback
from datetime import datetime, timedelta

import bots
from models import MessageToMessage, Server


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def _check_messages():
    api = bots.vk_bot.api
    chats = Server.all().order_by('chat_id').values_list('chat_id', flat=True)
    chats.distinct = True
    for chat_id in (await chats):
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_timestamp = int(yesterday.timestamp())
        messages = await (MessageToMessage
                          .filter(server__chat_id=chat_id,
                                  vk_timestamp__gt=yesterday_timestamp)
                          .values_list('vk_message_id', flat=True))
        for messages_chunk in chunk(messages, 100):
            checked_messages = await api.messages.get_by_conversation_message_id(
                peer_id=2000000000 + chat_id,
                conversation_message_ids=messages_chunk
            )
            if checked_messages.count == len(messages_chunk):
                continue
            else:
                messages_to_remove = messages_chunk.copy()
                for message in checked_messages.items:
                    messages_to_remove.remove(message.conversation_message_id)
                for message in messages_to_remove:
                    message_to_message = await MessageToMessage.get_or_none(
                        server__chat_id=chat_id,
                        vk_message_id=message
                    )
                    if not message_to_message:
                        continue
                    channel = bots.discord_bot.get_channel(
                        message_to_message.channel_id
                    )
                    if not channel:
                        continue
                    try:
                        discord_message = await channel.fetch_message(
                            message_to_message.discord_message_id
                        )
                        await discord_message.delete()
                    finally:
                        await message_to_message.delete()


async def check_messages_periodic(sleep_time):
    await asyncio.sleep(sleep_time)
    while True:
        try:
            await _check_messages()
        except Exception:
            traceback.print_exc()
        finally:
            await asyncio.sleep(sleep_time)

