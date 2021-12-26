import aiofiles
import config


async def format_help_message(filename):
    async with aiofiles.open(
            filename,
            mode='r',
            encoding='utf-8'
    ) as help_file:
        help_text = await help_file.read()
        help_text = help_text.format(
            vk_prefix=config.vk_prefix,
            discord_prefix=config.discord_prefix,
            alias_prefix=config.vk_alias_prefix
        )
        return help_text
