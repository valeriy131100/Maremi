import asyncio
import traceback

import aiosqlite
from disnake import NotFound

import bots
from datetime import datetime, timedelta

import db_helpers
from config import db_file


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def get_chats():
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT DISTINCT chat_id FROM MessageToMessage',
        )

        result = await cur.fetchall()
        return [row[0] for row in result]


async def get_unchecked_messages(chat_id):
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_timestamp = yesterday.timestamp()
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT vk_message_id '
            'FROM MessageToMessage '
            'WHERE (vk_timestamp > :timestamp or vk_timestamp is NULL) '
            'and chat_id = :chat_id',
            (yesterday_timestamp, chat_id)
        )
        result = await cur.fetchall()
        return [row[0] for row in result]


async def _check_messages():
    api = bots.vk_bot.api
    for chat_id in await get_chats():
        messages = await get_unchecked_messages(chat_id)
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
                    discord_message_raw = await db_helpers.get_discord_message(
                        chat_id=chat_id,
                        vk_message_id=message
                    )
                    if not discord_message_raw:
                        continue

                    channel_id, discord_message_id = discord_message_raw
                    channel = bots.discord_bot.get_channel(channel_id)
                    if not channel:
                        continue
                    try:
                        discord_message = await channel.fetch_message(
                            discord_message_id
                        )
                    except NotFound:
                        await db_helpers.remove_vk_message(
                            chat_id=chat_id,
                            vk_message_id=message
                        )
                        continue
                    await discord_message.delete()
                    await db_helpers.remove_vk_message(
                        chat_id=chat_id,
                        vk_message_id=message
                    )


async def check_messages_periodic(sleep_time):
    while True:
        try:
            await _check_messages()
        except Exception:
            traceback.print_exc()
        finally:
            await asyncio.sleep(sleep_time)
