from environs import Env

env = Env()
env.read_env()

vk_token = env('VK_TOKEN')
discord_token = env('DISCORD_TOKEN')
