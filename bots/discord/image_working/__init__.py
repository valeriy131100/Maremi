import disnake as discord
from disnake.ext import commands

import freeimagehost
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_channel_send_webhook
from bots.discord.utils.wrappers import react_and_delete


class SplitError(Exception):
    def __init__(self, message: discord.Message):
        self.message = message


class ImageWorking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @react_and_delete(exception=SplitError)
    async def split(self, context: commands.Context):
        if ref := context.message.reference:
            ref_message = await context.channel.fetch_message(ref.message_id)
            if attaches := ref_message.attachments:
                author_name = ref_message.author.display_name
                author_avatar = ref_message.author.avatar.url
                webhook = await get_channel_send_webhook(context.channel)
                first_embed = True
                for attach in attaches:
                    image_url = await freeimagehost.upload_and_get_url(
                        attach.url
                    )
                    timestamp = ref_message.created_at
                    embed = discord.Embed(timestamp=timestamp)
                    embed.set_image(url=image_url)
                    embed.set_author(name=author_name, icon_url=author_avatar)
                    if first_embed:
                        await webhook.send(
                            ref_message.content,
                            embed=embed,
                            username=author_name,
                            avatar_url=author_avatar
                        )
                        first_embed = False
                    else:
                        await webhook.send(
                            embed=embed,
                            username=author_name,
                            avatar_url=author_avatar
                        )
                await ref_message.delete()
            else:
                raise SplitError(message=context.message)
        else:
            raise SplitError(message=context.message)

    @commands.command(name='gallery')
    async def make_gallery(self, context: commands.Context, mode=None):
        original_message = None
        if ref := context.message.reference:
            message = await context.channel.fetch_message(ref.message_id)
            original_message = context.message
        else:
            message = context.message

        author_name = message.author.display_name
        author_avatar = message.author.avatar.url
        webhook = await get_channel_send_webhook(context.channel)

        images_count = len(message.attachments)
        if images_count < 2:
            await context.send(
                'Недостаточно вложений для создания галереи'
            )
            return
        gallery_message = await webhook.send(
            f'Загружаю {images_count} изображений',
            wait=True,
            username=author_name,
            avatar_url=author_avatar
        )
        gallery_images = [attachment.url for attachment in message.attachments]
        if mode in ('n', 'noninvite'):
            embeds, buttons = await create_gallery(
                gallery_images,
                invite_mode=False,
                use_multiple_preview=True
            )
        else:
            embed, buttons = await create_gallery(gallery_images)
            embeds = [embed]
        await message.delete()
        if original_message:
            await original_message.delete()
        await gallery_message.edit(content='', embeds=embeds, view=buttons)
