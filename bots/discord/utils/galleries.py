import traceback
from dataclasses import dataclass, asdict

import disnake as discord
from cache import AsyncLRU
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


@dataclass
class GalleryItem:
    image_url: str
    video_link: str = ''
    video_name: str = ''

    def __post_init__(self):
        if self.video_name and not self.video_link:
            raise ValueError
        if self.video_link and not self.video_name:
            raise ValueError


@AsyncLRU()
async def get_gallery_images(gallery_id: int) -> list[GalleryItem]:
    gallery_images = await (
        GalleryImages.filter(gallery_id=gallery_id)
                     .order_by('id')
                     .values('image_url', 'video_link', 'video_name')
    )

    return [GalleryItem(**gallery_image) for gallery_image in gallery_images]


async def clear_buttons_from_gallery(buttons: discord.ui.View) -> discord.ui.View:
    elems_to_remove = []

    for elem in buttons.children:
        try:
            if elem.custom_id.startswith(GALLERY):
                elems_to_remove.append(elem)
        except AttributeError:
            continue

    for elem in elems_to_remove:
        buttons.remove_item(elem)

    return buttons


def add_video_links(embed: discord.Embed, items: list[GalleryItem]) -> discord.Embed:
    video_links = [
        (num, item.video_link, item.video_name)
        for num, item in enumerate(items, start=1) if item.video_link
    ]

    if not video_links:
        return embed

    if len(video_links) == 1:
        name = "Ссылка на видео"
        formatted_links = (f"[{name}]({link})" for _, link, name in video_links)
    else:
        name = "Ссылки на видео"
        formatted_links = (f"{num}. [{name}]({link})" for num, link, name in video_links)

    embed.add_field(
        name=name,
        value="\n".join(formatted_links)
    )

    return embed


def add_video_link(embed, item: GalleryItem):
    return add_video_links(embed, [item])


def remove_video_links(embed: discord.Embed) -> tuple[discord.Embed, list[int]]:
    indexes = []
    for num, field in enumerate(embed.fields):
        if field.name in ('Ссылка на видео', 'Ссылки на видео'):
            embed.remove_field(num)
            indexes.append(num)

    return embed, indexes


async def get_gallery_message(attachment_id: int,
                              gallery_id: int,
                              embed: discord.Embed,
                              buttons: discord.ui.View) -> tuple[discord.Embed, discord.ui.View]:
    embed, _ = remove_video_links(embed)

    attachments: list[GalleryItem] = await get_gallery_images(gallery_id)
    attachments_count = len(attachments)

    attachment = attachments[attachment_id]
    embed.set_image(url=attachment.image_url)
    embed = add_video_link(embed, attachment)

    back_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label='Назад',
        custom_id=f'{GALLERY} {PREV} {attachment_id} {gallery_id}',
        row=4
    )
    num_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label=f'{attachment_id + 1}/{attachments_count}',
        custom_id=f'{GALLERY} {NUM} {attachment_id} {gallery_id}',
        row=4
    )
    next_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label='Вперёд',
        custom_id=f'{GALLERY} {NEXT} {attachment_id} {gallery_id}',
        row=4
    )

    buttons.add_item(back_button)
    buttons.add_item(num_button)
    buttons.add_item(next_button)

    return embed, buttons


async def get_expanded_gallery_message(gallery_id: int, embed: discord.Embed) -> list[discord.Embed]:
    attachments: list[GalleryItem] = await get_gallery_images(gallery_id)
    embeds = []
    author = embed.author
    first_embed = True

    remove_video_links(embed)

    for attachment in attachments:
        if first_embed:
            embeds.append(embed)
            first_embed = False
        else:
            attachment_embed = discord.Embed()
            attachment_embed.set_image(url=attachment.image_url)
            if author.name:
                attachment_embed.set_author(
                    name=author.name,
                    url=author.url,
                    icon_url=author.icon_url
                )
            add_video_link(embed, attachment)
            embeds.append(attachment_embed)

    return embeds


async def create_gallery(images: list[str | GalleryItem],
                         embed: discord.Embed | None = None,
                         buttons: discord.ui.View | None = None,
                         upload: bool = True,
                         use_multiple_preview: bool = False) -> tuple[list[discord.Embed], discord.ui.View]:
    for num, image in enumerate(images.copy()):
        if not isinstance(image, GalleryItem):
            images[num] = GalleryItem(image)

    images: list[GalleryItem]

    if upload:
        gallery_images_urls = await freeimagehost.multiple_upload_and_get_url(
            (image.image_url for image in images)
        )
        for image, uploaded_url in zip(images, gallery_images_urls):
            image.image_url = uploaded_url
    gallery_images = images

    max_id_gallery = await (GalleryImages
                            .annotate(max_id=Max('gallery_id'))
                            .first())
    if max_id_gallery.max_id is not None:
        gallery_id = max_id_gallery.max_id + 1
    else:
        gallery_id = 0

    gallery_image_objects = [
        GalleryImages(gallery_id=gallery_id, **asdict(image))
        for image in gallery_images
    ]

    await GalleryImages.bulk_create(objects=gallery_image_objects)

    if not embed:
        embed = discord.Embed()

    if not buttons:
        buttons = discord.ui.View()

    attachments: list[GalleryItem] = await get_gallery_images(gallery_id)
    attachments_count = len(attachments)

    attachment = attachments[0]
    embed.set_image(url=attachment.image_url)

    gallery_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label=f'Посмотреть как галерею ({attachments_count})',
        custom_id=f'{GALLERY} {SHOW} {0} {gallery_id}',
        row=4
    )
    all_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label=f'Посмотреть все сразу ({attachments_count})',
        custom_id=f'{GALLERY} {EXPAND} {0} {gallery_id}',
        row=4
    )

    buttons.add_item(gallery_button)
    buttons.add_item(all_button)

    embeds = []
    if not embed.url:
        embed.url = 'https://example.com'

    for i, image in enumerate(gallery_images[:3]):
        if i == 0:
            embeds.append(embed)
        else:
            preview_embed = discord.Embed(url=embed.url)
            preview_embed.set_image(url=image.image_url)
            embeds.append(preview_embed)

    add_video_links(embed, attachments)

    return embeds, buttons


class GalleriesHandler(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, interaction: discord.MessageInteraction) -> None:
        if interaction.component.custom_id.startswith(GALLERY):
            payload = interaction.component.custom_id
            _, command, attachment_id, gallery_id = payload.split()
            attachment_id = int(attachment_id)
            gallery_id = int(gallery_id)
            attachments = await get_gallery_images(gallery_id)

            message = interaction.message
            original_embed = interaction.message.embeds[0]
            original_buttons = await clear_buttons_from_gallery(
                discord.ui.View.from_message(message)
            )

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
                    attachment_id,
                    gallery_id,
                    original_embed,
                    original_buttons
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
                        attachment_id,
                        gallery_id,
                        original_embed,
                        original_buttons
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
