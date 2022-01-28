from datetime import datetime

import disnake as discord
from vkbottle_types.objects import WallWallComment

from .get_from import get_from_info

COMMENT_URL_TEMPLATE = ('https://vk.com/wall{group_id}_{post_id}'
                        '?reply={comment_id}')


async def make_comment_embed(comment: WallWallComment):
    comment_text = comment.text
    if comment_text and len(comment_text) > 4096:
        comment_text = f'{comment.text[:4093]}...'

    comment_link = COMMENT_URL_TEMPLATE.format(
        group_id=comment.owner_id,
        post_id=comment.post_id,
        comment_id=comment.id
    )

    comment_timestamp = datetime.utcfromtimestamp(comment.date)

    embed = discord.Embed(
        title=f'Комментарий к записи',
        url=comment_link,
        description=comment_text,
        timestamp=comment_timestamp
    )

    from_info = await get_from_info(comment.from_id)

    embed.set_author(
        name=from_info.name,
        icon_url=from_info.avatar_url,
        url=from_info.url
    )

    comment_stats = f'❤️  {comment.likes.count}'

    embed.add_field(
        name='⁠',
        value=comment_stats,
        inline=False
    )

    return embed
