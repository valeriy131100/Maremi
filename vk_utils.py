import random
from vkbottle import API


def get_random_id():
    return random.getrandbits(31) * random.choice([-1, 1])

