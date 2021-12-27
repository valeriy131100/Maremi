import disnake as discord
import freeimagehost
from disnake.ext import commands
from bots.discord.utils.galleries import create_gallery
from bots.discord.utils.webhooks import get_or_create_channel_send_webhook


class ImageWorking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def split(self, context: commands.Context):
        if ref := context.message.reference:
            ref_message = await context.channel.fetch_message(ref.message_id)
            if attaches := ref_message.attachments:
                author_name = ref_message.author.display_name
                author_avatar = ref_message.author.avatar.url
                webhook = await get_or_create_channel_send_webhook(
                    context.channel
                )
                first_embed = True
                for attach in attaches:
                    image_url = await freeimagehost.upload_and_get_url(attach.url)
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
                await context.message.delete()
            else:
                await context.send('Оригинальное сообщение не содержит изображений')
        else:
            await context.send('Пожалуйста, ответьте на сообщение, которое хотите разделить')

    @commands.command(name='gallery')
    async def make_gallery(self, context: commands.Context):
        original_message = None
        if ref := context.message.reference:
            message = await context.channel.fetch_message(ref.message_id)
            original_message = context.message
        else:
            message = context.message
        images_count = len(message.attachments)
        gallery_message = await context.send(f'Загружаю {images_count} изображений')
        gallery_images = [attachment.url for attachment in message.attachments]
        embed, buttons = await create_gallery(gallery_images)
        await message.delete()
        if original_message:
            await original_message.delete()
        await gallery_message.edit(content='', embed=embed, view=buttons)
