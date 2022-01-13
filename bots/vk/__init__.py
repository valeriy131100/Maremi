import vkbottle.bot

from bots.help_message_formatter import format_help_message
from config import vk_token

from .custom_rules import StartsWithRule
from .vk_to_discord import bp as vk_to_discord_bp


def load_child_bps(bps, bot):
    for bp in bps:
        bp.load(bot)
        if hasattr(bp, 'child_bps'):
            load_child_bps(bp.child_bps, bot)


vk_bot = vkbottle.bot.Bot(vk_token)
load_child_bps([vk_to_discord_bp], vk_bot)


@vk_bot.on.chat_message(StartsWithRule('help', return_text=False))
async def help_(message: vkbottle.bot.Message):
    help_text = await format_help_message('vk_help_message.txt')
    await message.answer(help_text)
        