import random
from typing import Optional, List

from vkbottle_types.objects import PhotosPhotoSizesType as SizeType


def get_random_id():
    return random.getrandbits(31) * random.choice([-1, 1])


def get_photo_max_size(photo_sizes: Optional[List[SizeType]]):
    if not photo_sizes:
        return

    keys = (SizeType.S, SizeType.M, SizeType.X, SizeType.Y, SizeType.Z, SizeType.W)

    max_size = max(
        photo_sizes,
        key=lambda size: keys.index(size.type) if size.type in keys else -1
    )

    return max_size