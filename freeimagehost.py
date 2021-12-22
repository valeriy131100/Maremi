import aiohttp
from config import freeimagehost_key


async def upload_and_get_url(image_url):
    imgbb_url = 'https://freeimage.host/api/1/upload'
    params = {
        'key': freeimagehost_key,
        'image': image_url
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(imgbb_url, params=params) as resp:
            if resp.status == 200:
                image = await resp.json()
                return image['image']['url']
