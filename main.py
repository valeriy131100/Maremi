from pathlib import Path
import asyncio
from bots import discord_bot
from bots import vk_bot
from bots.vk.message_checker import check_messages_periodic

from config import discord_token, db_file, vk_check_messages_interval
import db_helpers

if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    if not Path(db_file).is_file():
        loop.run_until_complete(db_helpers.create_db())

    check_messages_task = loop.create_task(
        check_messages_periodic(vk_check_messages_interval)
    )

    loop.run_until_complete(
        asyncio.gather(
            discord_bot.start(discord_token),
            vk_bot.run_polling(),
            check_messages_task
        )
    )
