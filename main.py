from pathlib import Path
import asyncio
from bots import discord_bot
from bots import vk_bot

from config import discord_token, db_file
import db_helpers

if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    if not Path(db_file).is_file():
        loop.run_until_complete(db_helpers.create_db())

    loop.run_until_complete(
        asyncio.gather(
            discord_bot.start(discord_token),
            vk_bot.run_polling()
        )
    )
