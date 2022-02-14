import disnake as discord
from disnake.ext import commands

import freeimagehost
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_channel_send_webhook
from bots.discord.utils.wrappers import react_loading, react_success_and_delete
from bots.discord.utils.wrappers.ref_message import (
    use_content_message_context,
    ContentMessageContext
)


class SplitError(Exception):
    def __init__(self, message: discord.Message):
        self.message = message


class GalleryError(Exception):
    def __init__(self, message: discord.Message):
        self.message = message


class ImageWorking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @react_success_and_delete(exception=SplitError, success_delete_delay=0)
    @react_loading
    async def split(self, context: commands.Context):
        message = context.message

        if not (ref := context.message.reference):
            raise SplitError(message=message)

        ref_message = await context.channel.fetch_message(ref.message_id)

        if not (attachments := ref_message.attachments):
            raise SplitError(message=message)

        author_name = ref_message.author.display_name
        author_avatar = ref_message.author.avatar.url
        timestamp = ref_message.created_at
        webhook = await get_channel_send_webhook(context.channel)

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

    @commands.command(name='gallery')
    @use_content_message_context
    @react_success_and_delete(exception=GalleryError, success_delete_delay=0)
    @react_loading
    async def make_gallery(self, context: ContentMessageContext, mode=None):
        message = context.content_message

        author_name = message.author.display_name
        author_avatar = message.author.avatar.url
        webhook = await get_channel_send_webhook(context.channel)
        attachments = message.attachments

        if len(attachments) < 2:
            raise GalleryError(message=message)

        gallery_images = [attachment.url for attachment in attachments]

        invite_mode = mode not in ('n', 'noninvite')

        embeds, buttons = await create_gallery(
            gallery_images,
            invite_mode=invite_mode,
            use_multiple_preview=True
        )

        await webhook.send(
            embeds=embeds,
            username=author_name,
            avatar_url=author_avatar,
            view=buttons
        )
