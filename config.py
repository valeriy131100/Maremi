from environs import Env

env = Env()
env.read_env()

vk_token = env('VK_TOKEN')
vk_prefix = env('VK_PREFIX', default='/')
vk_alias_prefix = env('VK_ALIAS_PREFIX', default='#')
vk_group_id = env.int('VK_GROUP_ID')
vk_check_messages_interval = env.int('VK_CHECK_MESSAGES_INTERVAL', default=60)

discord_token = env('DISCORD_TOKEN')
discord_prefix = env('DISCORD_PREFIX', default='m.')

spotify_client_id = env('SPOTIFY_CLIENT_ID')
spotify_client_secret = env('SPOTIFY_CLIENT_SECRET')

db_file = env('DATABASE', default='sqlite://servers2.db')
freeimagehost_key = env('FREEIMAGEHOST_KEY')

TORTOISE_ORM = {
    "connections": {"default": db_file},
    "apps": {
        "models": {
            "models": ["aerich.models", "models"],
            "default_connection": "default",
        },
    },
}
