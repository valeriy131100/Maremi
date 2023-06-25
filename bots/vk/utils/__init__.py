import random

from vkbottle_types.codegen.objects import VideoVideoImage, PhotosPhotoSizes
from vkbottle_types.objects import PhotosPhotoSizesType as SizeType


def get_random_id() -> int:
    return random.getrandbits(31) * random.choice([-1, 1])


PHOTO_KEYS = (SizeType.S, SizeType.M, SizeType.X, SizeType.Y, SizeType.Z, SizeType.W)


def get_photo_max_size(photo_sizes: list[PhotosPhotoSizes] | None) -> PhotosPhotoSizes | None:
    if not photo_sizes:
        return

    max_size = max(
        photo_sizes,
        key=lambda size: PHOTO_KEYS.index(size.type) if size.type in PHOTO_KEYS else -1
    )

    return max_size


def get_video_max_size(video_images: list[VideoVideoImage] | None) -> VideoVideoImage | None:
    if not video_images:
        return

    return max(
        video_images,
        key=lambda image: image.width
    )
