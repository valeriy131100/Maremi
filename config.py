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

db_file = env('DATABASE', default='servers.db')
freeimagehost_key = env('FREEIMAGEHOST_KEY')
