import disnake as discord
import bots
import freeimagehost
from disnake.ext import commands
from .galleries import ImageWorkingGalleries


class ImageWorking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_cog(ImageWorkingGalleries(bot))

    @commands.command()
    async def split(self, context: commands.Context):
        if ref := context.message.reference:
            ref_message = await context.channel.fetch_message(ref.message_id)
            if attaches := ref_message.attachments:
                author_name = ref_message.author.display_name
                author_avatar = ref_message.author.avatar.url
                webhook = await context.channel.create_webhook(name=author_name)
                bots.temp['webhooks'].append(webhook.id)
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
                await webhook.delete()
                await ref_message.delete()
                await context.message.delete()
            else:
                await context.send('Оригинальное сообщение не содержит изображений')
        else:
            await context.send('Пожалуйста, ответьте на сообщение, которое хотите разделить')