import random
from vkbottle import API


def get_random_id():
    return random.getrandbits(31) * random.choice([-1, 1])


async def get_user_photo(user_id, vk_api: API):
    response = await vk_api.users.get(fields=['photo50'])
    print(response)

