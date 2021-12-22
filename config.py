from environs import Env

env = Env()
env.read_env()

vk_token = env('VK_TOKEN')
discord_token = env('DISCORD_TOKEN')
db_file = env('DATABASE', default='servers.db')
freeimagehost_key = env('FREEIMAGEHOST_KEY')
