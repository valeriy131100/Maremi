from disnake import Guild, TextChannel, Webhook


async def get_channel_send_webhook(channel: TextChannel) -> Webhook:
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name.startswith('MaremiSendWebhook'):
            return webhook
    else:
        return await channel.create_webhook(
            name=f'MaremiSendWebhook'
        )


async def get_server_bot_webhooks_ids(server: Guild):
    webhooks = await server.webhooks()
    bot_webhooks_ids = []
    for webhook in webhooks:
        if webhook.name.startswith('Maremi'):
            bot_webhooks_ids.append(webhook.id)

    return bot_webhooks_ids
