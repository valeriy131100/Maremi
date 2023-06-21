import disnake as discord
from disnake.ext import commands

import freeimagehost
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_channel_send_webhook

from bots.discord.base import CommandInteraction


class SplitError(Exception):
    def __init__(self, message: discord.Message):
        self.message = message


class GalleryError(Exception):
    def __init__(self, message: discord.Message):
        self.message = message


class ImageWorking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Разделить вложения")
    async def split(self, inter: CommandInteraction) -> None:
        ref_message = inter.target

        await inter.response.defer(ephemeral=True)

        if not (attachments := ref_message.attachments):
            await inter.edit_original_response("Невозможно разделить сообщение без вложений")

        author_name = ref_message.author.display_name
        author_avatar = ref_message.author.avatar.url
        timestamp = ref_message.created_at
        webhook = await get_channel_send_webhook(ref_message.channel)

        images_urls = await freeimagehost.multiple_upload_and_get_url(
            [attachment.url for attachment in attachments]
        )

        first_embed = True
        embeds = []
        embed = discord.Embed(timestamp=timestamp)
        embed.set_author(name=author_name, icon_url=author_avatar)
        for image_url in images_urls:
            image_embed = embed.copy()
            image_embed.set_image(image_url)

            if first_embed:
                image_embed.description = ref_message.content
                embeds.append(image_embed)
                first_embed = False
            else:
                embeds.append(image_embed)

        await webhook.send(
            embeds=embeds,
            username=author_name,
            avatar_url=author_avatar
        )

        await ref_message.delete()

        await inter.delete_original_response()

    @commands.message_command(name="Сделать галереей")
    async def make_gallery(self, inter: "CommandInteraction") -> None:
        await inter.response.defer(ephemeral=True)

        message = inter.target

        author_name = message.author.display_name
        author_avatar = None
        if message.author.avatar:
            author_avatar = message.author.avatar.url
        webhook = await get_channel_send_webhook(message.channel)
        attachments = message.attachments

        if len(attachments) < 2:
            await inter.edit_original_response("Недостаточно изображений для создания галереи")
            return

        gallery_images = [attachment.url for attachment in attachments]

        embeds, buttons = await create_gallery(
            gallery_images,
            use_multiple_preview=True
        )

        await webhook.send(
            embeds=embeds,
            username=author_name,
            avatar_url=author_avatar,
            view=buttons
        )

        await inter.delete_original_response()
