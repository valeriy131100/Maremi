from dataclasses import dataclass

import bots

FROM_USER_TEMPLATE = 'https://vk.com/id{from_id}'
FROM_GROUP_TEMPLATE = 'https://vk.com/club{from_id}'


@dataclass
class FromInfo:
    name: str
    avatar_url: str
    url: str


async def get_from_info(from_id):
    if from_id < 0:
        group_info = await bots.vk_bot.api.groups.get_by_id(
            group_id=str(abs(from_id))
        )
        return FromInfo(
            name=group_info[0].name,
            avatar_url=group_info[0].photo_200,
            url=FROM_GROUP_TEMPLATE.format(from_id=abs(from_id))
        )
    else:
        user_info = await bots.vk_bot.api.users.get(
            user_ids=[from_id], fields=['photo_200']
        )
        return FromInfo(
            name=f'{user_info[0].first_name} {user_info[0].last_name}',
            avatar_url=user_info[0].photo_200,
            url=FROM_USER_TEMPLATE.format(from_id=from_id)
        )
