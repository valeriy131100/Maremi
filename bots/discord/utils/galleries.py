import disnake as discord
import db_helpers
import freeimagehost
from disnake.ext import commands


async def get_gallery_message(attachment_id, gallery_id):
    attachments = await db_helpers.get_gallery_images(gallery_id)
    images_count = len(attachments)
    buttons = discord.ui.View()
    back_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label='Назад',
        custom_id=f'gallery prev {attachment_id} {gallery_id}',
    )
    num_button = discord.ui.Button(
        style=discord.ButtonStyle.secondary,
        label=f'{attachment_id + 1}/{images_count}',
        custom_id=f'gallery num {attachment_id} {gallery_id}'
    )
    next_button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label='Вперёд',
        custom_id=f'gallery next {attachment_id} {gallery_id}',
    )

    buttons.add_item(back_button)
    buttons.add_item(num_button)
    buttons.add_item(next_button)

    embed = discord.Embed()
    embed.set_image(url=attachments[attachment_id])

    return embed, buttons


async def create_gallery(images, start_id=0):
    gallery_images = await freeimagehost.multiple_upload_and_get_url(
        images
    )
    gallery_id = await db_helpers.create_gallery(gallery_images)
    return await get_gallery_message(start_id, gallery_id)


class GalleriesHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        if interaction.component.custom_id.startswith('gallery'):
            payload = interaction.component.custom_id
            _, command, attachment_id, gallery_id = payload.split()
            attachment_id = int(attachment_id)
            gallery_id = int(gallery_id)
            attachments = await db_helpers.get_gallery_images(gallery_id)

            if command == 'next':
                if attachment_id == len(attachments) - 1:
                    attachment_id = 0
                else:
                    attachment_id += 1
            elif command == 'prev':
                if attachment_id == 0:
                    attachment_id = len(attachments) - 1
                else:
                    attachment_id -= 1

            embed, buttons = await get_gallery_message(
                attachment_id, gallery_id
            )
            await interaction.response.edit_message(embed=embed, view=buttons)
