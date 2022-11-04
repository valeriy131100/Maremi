import asyncio
import logging

from tortoise import Tortoise

import config
from bots import discord_bot, vk_bot
from bots.vk.message_checker import check_messages_periodic

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)

    loop = asyncio.get_event_loop()

    check_messages_task = loop.create_task(
        check_messages_periodic(config.vk_check_messages_interval)
    )

    try:
        loop.run_until_complete(
            asyncio.gather(
                Tortoise.init(config=config.TORTOISE_ORM),
                discord_bot.start(config.discord_token),
                vk_bot.run_polling(),
                check_messages_task
            )
        )
    finally:
        asyncio.run(Tortoise.close_connections())
