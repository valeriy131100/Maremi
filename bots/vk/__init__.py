import aiofiles
import vkbottle.bot
from config import vk_token
from .vk_to_discord import bp as vk_to_discord_bp
from .custom_rules import StartsWithRule


def load_child_bps(bps, bot):
    for bp in bps:
        bp.load(bot)
        if hasattr(bp, 'child_bps'):
            load_child_bps(bp.child_bps, bot)


vk_bot = vkbottle.bot.Bot(vk_token)
load_child_bps([vk_to_discord_bp], vk_bot)


@vk_bot.on.chat_message(StartsWithRule('help', return_text=False))
async def help_(message: vkbottle.bot.Message):
    async with aiofiles.open('vk_help_message.txt', mode='r', encoding='utf-8') as help_file:
        help_text = await help_file.read()
        await message.answer(help_text)
        