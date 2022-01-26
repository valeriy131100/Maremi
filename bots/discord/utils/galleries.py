import disnake as discord
from disnake.ext import commands
from tortoise.functions import Max

import freeimagehost
from models import GalleryImages

GALLERY = 'gallery'
PREV = 'prev'
NUM = 'num'
NEXT = 'next'
SHOW = 'show'
EXPAND = 'expand'


cached_galleries = {
    # gallery_id: gallery_images
}


async def get_gallery_images(gallery_id):
    if gallery_images := cached_galleries.get(gallery_id):
        return gallery_images
    else:
        gallery_images = await (
            GalleryImages.filter(gallery_id=gallery_id)
                         .order_by('id')
                         .values_list('image_url', flat=True)
        )
        cached_galleries[gallery_id] = gallery_images
        return gallery_images


async def get_gallery_message(attachment_id, gallery_id, embed: discord.Embed):
    attachments = await get_gallery_images(gallery_id)
    images_count = len(attachments)
    buttons = discord.ui.View()
    back_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label='Назад',
        custom_id=f'{GALLERY} {PREV} {attachment_id} {gallery_id}',
    )
    num_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label=f'{attachment_id + 1}/{images_count}',
        custom_id=f'{GALLERY} {NUM} {attachment_id} {gallery_id}'
    )
    next_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label='Вперёд',
        custom_id=f'{GALLERY} {NEXT} {attachment_id} {gallery_id}',
    )

    buttons.add_item(back_button)
    buttons.add_item(num_button)
    buttons.add_item(next_button)

    embed.set_image(url=attachments[attachment_id])

    return embed, buttons


async def get_gallery_invite_message(attachment_id, gallery_id,
                                     embed: discord.Embed):
    attachments = await get_gallery_images(gallery_id)
    attachments_count = len(attachments)
    buttons = discord.ui.View()
    back_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label=f'Посмотреть как галерею ({attachments_count})',
        custom_id=f'{GALLERY} {SHOW} {attachment_id} {gallery_id}',
    )
    next_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label=f'Посмотреть все сразу ({attachments_count})',
        custom_id=f'{GALLERY} {EXPAND} {attachment_id} {gallery_id}',
    )

    buttons.add_item(back_button)
    buttons.add_item(next_button)

    embed.set_image(url=attachments[attachment_id])

    return embed, buttons


async def get_expanded_gallery_message(gallery_id, embed: discord.Embed):
    attachments = await get_gallery_images(gallery_id)
    embeds = []
    author = embed.author
    first_embed = True
    for attachment in attachments:
        if first_embed:
            embeds.append(embed)
            first_embed = False
        else:
            attachment_embed = discord.Embed()
            attachment_embed.set_image(url=attachment)
            if author.name:
                attachment_embed.set_author(
                    name=author.name,
                    url=author.url,
                    icon_url=author.icon_url
                )
            embeds.append(attachment_embed)

    return embeds


async def create_gallery(images, embed=None, upload=True, invite_mode=False,
                         use_multiple_preview=False):
    if upload:
        gallery_images = await freeimagehost.multiple_upload_and_get_url(
            images
        )
    else:
        gallery_images = images

    max_id_gallery = await (GalleryImages
                            .annotate(max_id=Max('gallery_id'))
                            .first())
    if max_id_gallery.max_id is not None:
        gallery_id = max_id_gallery.max_id + 1
    else:
        gallery_id = 0

    gallery_image_objects = [
        GalleryImages(gallery_id=gallery_id, image_url=image_url)
        for image_url in gallery_images
    ]

    await GalleryImages.bulk_create(objects=gallery_image_objects)

    if not embed:
        embed = discord.Embed()

    if invite_mode:
        embed, buttons = await get_gallery_invite_message(0, gallery_id, embed)
    else:
        embed, buttons = await get_gallery_message(0, gallery_id, embed)

    if not use_multiple_preview:
        return embed, buttons
    else:
        embeds = []
        if not embed.url:
            embed.url = 'https://example.com'

        for i, image_url in enumerate(gallery_images[:3]):
            if i == 0:
                embeds.append(embed)
            else:
                preview_embed = discord.Embed(url=embed.url)
                preview_embed.set_image(url=image_url)
                embeds.append(preview_embed)

        return embeds, buttons


class GalleriesHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, interaction: discord.MessageInteraction):
        if interaction.component.custom_id.startswith(GALLERY):
            payload = interaction.component.custom_id
            _, command, attachment_id, gallery_id = payload.split()
            attachment_id = int(attachment_id)
            gallery_id = int(gallery_id)
            attachments = await get_gallery_images(gallery_id)
            original_embed = interaction.message.embeds[0]

            if command in (NEXT, PREV):
                if command == NEXT:
                    if attachment_id == len(attachments) - 1:
                        attachment_id = 0
                    else:
                        attachment_id += 1
                elif command == PREV:
                    if attachment_id == 0:
                        attachment_id = len(attachments) - 1
                    else:
                        attachment_id -= 1

                embed, buttons = await get_gallery_message(
                    attachment_id, gallery_id, original_embed
                )
                await interaction.response.edit_message(
                    embed=embed,
                    view=buttons
                )
            elif command == NUM:
                await interaction.response.defer()
            elif command in (SHOW, EXPAND):
                if command == SHOW:
                    embed, buttons = await get_gallery_message(
                        attachment_id, gallery_id, original_embed
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        view=buttons,
                        ephemeral=True
                    )
                elif command == EXPAND:
                    embeds = await get_expanded_gallery_message(
                        gallery_id, original_embed
                    )

                    await interaction.response.send_message(
                        embeds=embeds,
                        ephemeral=True
                    )

