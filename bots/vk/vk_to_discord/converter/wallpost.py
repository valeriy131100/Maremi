from datetime import datetime

import disnake as discord
from vkbottle_types.objects import WallWallpostFull

from .get_from import get_from_info

POST_URL_TEMPLATE = 'https://vk.com/wall{from_id}_{post_id}'


async def make_post_embed(post: WallWallpostFull):
    post_text = post.text
    if post_text and len(post_text) > 4096:
        post_text = f'{post.text[:4093]}...'

    post_link = POST_URL_TEMPLATE.format(
        from_id=post.from_id,
        post_id=post.id
    )

    post_timestamp = datetime.utcfromtimestamp(post.date)

    embed = discord.Embed(
        title=f'Запись на стене',
        url=post_link,
        description=post_text,
        timestamp=post_timestamp
    )

    from_info = await get_from_info(post.from_id)

    embed.set_author(
        name=from_info.name,
        icon_url=from_info.avatar_url,
        url=from_info.url
    )

    post_stats = (f'❤️  {post.likes.count}  '
                  f'💬  {post.comments.count}  '
                  f'🔁  {post.reposts.count}')

    embed.add_field(
        name='⁠',
        value=post_stats,
        inline=False
    )

    return embed
