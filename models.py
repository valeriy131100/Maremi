from tortoise.models import Model
from tortoise import fields


class Server(Model):
    server_id = fields.IntField(pk=True)
    server_default_channel = fields.IntField(null=True)
    default_image_channel = fields.IntField(null=True)
    duplex_channel = fields.IntField(null=True)
    chat_id = fields.IntField(null=True)


class ServerChannelAlias(Model):
    server = fields.ForeignKeyField('models.Server')
    channel_id = fields.IntField()
    alias = fields.CharField(max_length=100)


class DiscordNickName(Model):
    discord_id = fields.IntField(pk=True)
    nickname = fields.CharField(max_length=100)


class VkNickName(Model):
    vk_id = fields.IntField(pk=True)
    nickname = fields.CharField(max_length=100)


class GalleryImages(Model):
    gallery_id = fields.IntField()
    image_url = fields.TextField()


class MessageToMessage(Model):
    server = fields.ForeignKeyField('models.Server')
    channel_id = fields.IntField()
    discord_message_id = fields.IntField()
    vk_message_id = fields.IntField()
    vk_timestamp = fields.IntField()

    class Meta:
        unique_together = (
            ('channel_id', 'discord_message_id')
        )