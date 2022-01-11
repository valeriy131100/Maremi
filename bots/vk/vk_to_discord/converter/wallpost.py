from datetime import datetime

import disnake as discord
from vkbottle_types.objects import WallWallpostFull

import bots

POST_URL_TEMPLATE = 'https://vk.com/wall{from_id}_{post_id}'
FROM_USER_TEMPLATE = 'https://vk.com/id{from_id}'
FROM_GROUP_TEMPLATE = 'https://vk.com/club{from_id}'


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

    from_name, from_avatar, from_url = (
        await get_from_info_from_wall_post(post)
    )

    embed.set_author(
        name=from_name,
        icon_url=from_avatar,
        url=from_url
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


async def get_from_info_from_wall_post(post: WallWallpostFull):
    from_id = post.from_id
    if from_id < 0:
        group_info = await bots.vk_bot.api.groups.get_by_id(
            group_id=str(abs(from_id))
        )
        group_name = group_info[0].name
        group_avatar = group_info[0].photo_200
        group_url = FROM_GROUP_TEMPLATE.format(from_id=abs(post.from_id))
        return group_name, group_avatar, group_url
    else:
        user_info = await bots.vk_bot.api.users.get(
            user_ids=[from_id], fields=['photo_200']
        )
        user_name = f'{user_info[0].first_name} {user_info[0].last_name}'
        user_avatar = user_info[0].photo_200
        user_url = FROM_USER_TEMPLATE.format(from_id=post.from_id)
        return user_name, user_avatar, user_url
