from environs import Env

env = Env()
env.read_env()

vk_token = env('VK_TOKEN')
vk_prefix = env('VK_PREFIX', default='/')

discord_token = env('DISCORD_TOKEN')
discord_prefix = env('DISCORD_PREFIX', defualt='m.')

db_file = env('DATABASE', default='servers.db')
freeimagehost_key = env('FREEIMAGEHOST_KEY')
