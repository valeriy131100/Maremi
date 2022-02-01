from dataclasses import dataclass

import bots
from models import VkNickName

FROM_USER_TEMPLATE = 'https://vk.com/id{from_id}'
FROM_GROUP_TEMPLATE = 'https://vk.com/club{from_id}'


@dataclass
class FromInfo:
    from_id: int
    name: str
    avatar_url: str
    url: str

    def __post_init__(self):
        self.nickname = None

    async def load_nickname(self):
        if self.from_id < 0:
            self.nickname = self.name
        else:
            user_nickname = await VkNickName.get_or_none(vk_id=self.from_id)
            if user_nickname:
                user_nickname = user_nickname.nickname
            else:
                user_nickname = None
            self.nickname = (self.name if not user_nickname
                             else f'{user_nickname.nickname} ({self.name})')


async def get_from_info(from_id):
    if from_id < 0:
        group_info = (await bots.vk_bot.api.groups.get_by_id(
            group_id=abs(from_id)
        ))[0]
        from_info = FromInfo(
            from_id=from_id,
            name=group_info.name,
            avatar_url=group_info.photo_200,
            url=FROM_GROUP_TEMPLATE.format(from_id=abs(from_id))
        )
        return from_info
    else:
        user_info = (await bots.vk_bot.api.users.get(
            user_ids=[from_id], fields=['photo_200']
        ))[0]
        user_name = f'{user_info.first_name} {user_info.last_name}'

        from_info = FromInfo(
            from_id=from_id,
            name=user_name,
            avatar_url=user_info.photo_200,
            url=FROM_USER_TEMPLATE.format(from_id=from_id)
        )

        return from_info

