import asyncio

import aiohttp
from config import freeimagehost_key


async def _get_image_url(image_url, session):
    url = 'https://freeimage.host/api/1/upload'
    params = {
        'key': freeimagehost_key,
        'image': image_url
    }

    async with session.get(url, params=params) as response:
        if response.status == 200:
            image = await response.json()
            return image['image']['url']


async def upload_and_get_url(image_url):
    async with aiohttp.ClientSession() as session:
        return await _get_image_url(image_url, session)


async def multiple_upload_and_get_url(images_urls):
    tasks = []

    async with aiohttp.ClientSession() as session:
        for image_url in images_urls:
            task = asyncio.ensure_future(_get_image_url(image_url, session))
            tasks.append(task)

        uploaded_urls = await asyncio.gather(*tasks)
        return uploaded_urls

