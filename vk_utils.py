import random


def get_random_id():
    """ Get random int32 number (signed) """
    return random.getrandbits(31) * random.choice([-1, 1])
