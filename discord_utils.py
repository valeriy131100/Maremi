import aiohttp
import aiofiles
import re


EMOJI_REGEX = re.compile(r'(<(a?):\w+:(\d{18})>)')
EMOJI_URL_TEMPLATE = 'https://cdn.discordapp.com/emojis/{emoji_id}.png?size=128'


async def download_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(filename, mode='wb')
                await f.write(await resp.read())
                await f.close()
                return filename


async def download_emoji(emoji_id, guild_id):
    url = EMOJI_URL_TEMPLATE.format(emoji_id=emoji_id)
    filename = f'{guild_id}_{emoji_id}.png'
    return await download_file(url, filename)

