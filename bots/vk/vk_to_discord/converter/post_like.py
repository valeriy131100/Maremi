from datetime import datetime
from typing import Union

import disnake as discord
from vkbottle_types.objects import WallWallpostFull, WallWallComment

from .get_from import get_from_info

POST_URL_TEMPLATE = 'https://vk.com/wall{from_id}_{post_id}'
COMMENT_URL_TEMPLATE = ('https://vk.com/wall{group_id}_{post_id}'
                        '?reply={comment_id}')
PostLike = Union[WallWallpostFull, WallWallComment]


async def make_basic_post_like_embed(post_like: PostLike):
    text = post_like.text
    if text and len(text) > 4096:
        text = f'{post_like.text[:4093]}...'

    timestamp = datetime.utcfromtimestamp(post_like.date)

    embed = discord.Embed(
        description=text,
        timestamp=timestamp
    )

    from_info = await get_from_info(post_like.from_id)

    embed.set_author(
        name=from_info.name,
        icon_url=from_info.avatar_url,
        url=from_info.url
    )

    return embed


async def make_post_embed(post: WallWallpostFull):
    embed = await make_basic_post_like_embed(post)
    embed.title = 'Запись на стене'
    embed.url = POST_URL_TEMPLATE.format(
        from_id=post.from_id,
        post_id=post.id
    )

    buttons = discord.ui.View()
    buttons.add_item(
        discord.ui.Button(
            label=f'❤️  {post.likes.count}  '
        )
    )
    buttons.add_item(
        discord.ui.Button(
            label=f'💬  {post.comments.count}  '
        )
    )
    buttons.add_item(
        discord.ui.Button(
            label=f'🔁  {post.reposts.count}  '
        )
    )

    return embed, buttons


async def make_comment_embed(comment: WallWallComment):
    embed = await make_basic_post_like_embed(comment)

    embed.title = 'Комментарий к записи'
    embed.url = COMMENT_URL_TEMPLATE.format(
        group_id=comment.owner_id,
        post_id=comment.post_id,
        comment_id=comment.id
    )

    buttons = discord.ui.View()
    buttons.add_item(
        discord.ui.Button(
            label=f'❤️  {comment.likes.count}  '
        )
    )
    if comment.thread:
        buttons.add_item(
            discord.ui.Button(
                label=f'💬  {comment.thread.count}  '
            )
        )

    return embed, buttons