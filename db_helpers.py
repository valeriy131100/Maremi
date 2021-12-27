import aiosqlite
import aiofiles
import disnake as discord
from config import db_file
from aiosqlite import IntegrityError


async def create_db():
    async with aiosqlite.connect(db_file) as db, aiofiles.open('createdb.sql', 'r') as create_sql:
        cur = await db.cursor()
        await cur.executescript(await create_sql.read())


async def connect_server_to_chat(server_id, chat_id, default_channel):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        try:
            await cur.execute(
                'INSERT INTO Server (server_id, server_default_channel) VALUES (?, ?)',
                (server_id, default_channel)
            )
        except IntegrityError:
            await cur.execute(
                'UPDATE Server SET server_default_channel = ? WHERE server_id = ?',
                (default_channel, server_id)
            )
            await cur.execute(
                'UPDATE ServerToChat SET chat_id = ? WHERE server_id = ?',
                (chat_id, server_id)
            )
        else:
            await cur.execute(
                'INSERT INTO ServerToChat (server_id, chat_id) VALUES (?, ?)',
                (server_id, chat_id)
            )
        await db.commit()


async def get_chat_server(chat_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT server_id FROM ServerToChat WHERE chat_id=?', (chat_id, )
        )
        server_id = await cur.fetchone()
        if server_id:
            return server_id[0]


async def get_server_chat(server_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT chat_id FROM ServerToChat WHERE server_id=?', (server_id, )
        )
        chat_id = (await cur.fetchone())[0]
        return chat_id


async def get_default_channel(server_id=None, chat_id=None):
    if not (server_id or chat_id):
        return
    else:
        if server_id:
            async with aiosqlite.connect(db_file) as db:
                cur = await db.cursor()
                await cur.execute(
                    'SELECT server_default_channel FROM Server WHERE server_id=?', (server_id,)
                )
                return (await cur.fetchone())[0]
        else:
            server_id = await get_chat_server(chat_id)
            return await get_default_channel(server_id=server_id)


async def get_default_image_channel(server_id=None, chat_id=None):
    if not (server_id or chat_id):
        return
    else:
        if server_id:
            async with aiosqlite.connect(db_file) as db:
                cur = await db.cursor()
                await cur.execute(
                    'SELECT default_image_channel FROM Server WHERE server_id=?', (server_id,)
                )
                result = (await cur.fetchone())[0]
                if result:
                    return result
                else:
                    return await get_default_channel(server_id=server_id)
        else:
            server_id = await get_chat_server(chat_id)
            return await get_default_image_channel(server_id=server_id)


async def set_default_channel(server_id, channel_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'UPDATE Server SET server_default_channel=? where server_id=?',
            (channel_id, server_id)
        )
        await db.commit()


async def set_default_image_channel(server_id, channel_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'UPDATE Server SET default_image_channel=? where server_id=?',
            (channel_id, server_id)
        )
        await db.commit()


async def make_alias(server_id, channel_id, alias):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'INSERT INTO ServerChannelAlias (server_id, channel_id, alias) VALUES (?, ?, ?)',
            (server_id, channel_id, alias)
        )
        await db.commit()


async def delete_alias(server_id, alias):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT alias FROM ServerChannelAlias where server_id=? and alias=?',
            (server_id, alias)
        )
        result = await cur.fetchone()
        if result:
            await cur.execute(
                'DELETE FROM ServerChannelAlias WHERE server_id=? and alias=?',
                (server_id, alias)
            )
            await db.commit()
        else:
            raise IndexError


async def get_aliases(server_id=None, chat_id=None):
    if not (server_id or chat_id):
        return
    else:
        if server_id:
            async with aiosqlite.connect(db_file) as db:
                cur = await db.cursor()
                await cur.execute(
                    'SELECT alias FROM ServerChannelAlias where server_id=?', (server_id,)
                )
                fetched = await cur.fetchall()
                aliases = [row[0] for row in fetched]
                return aliases if aliases else []
        else:
            server_id = await get_chat_server(chat_id)
            return await get_aliases(server_id=server_id)


async def get_channel_by_alias(alias, server_id=None, chat_id=None):
    if not (server_id or chat_id):
        return
    else:
        if server_id:
            async with aiosqlite.connect(db_file) as db:
                cur = await db.cursor()
                await cur.execute(
                    'SELECT channel_id FROM ServerChannelAlias where alias=?', (alias,)
                )
                return (await cur.fetchone())[0]
        else:
            server_id = await get_chat_server(chat_id)
            return await get_channel_by_alias(alias, server_id=server_id)


async def set_duplex_channel(server_id, channel_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'UPDATE Server SET duplex_channel=? where server_id=?',
            (channel_id, server_id)
        )
        await db.commit()


async def is_duplex_channel(server_id, channel_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT server_id from Server where server_id=? and duplex_channel=?',
            (server_id, channel_id)
        )
        result = await cur.fetchone()
        return bool(result)


async def get_chat_duplex_channel(chat_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT duplex_channel from ServerToChat stc, Server s where stc.server_id = s.server_id and chat_id=?',
            (chat_id,)
        )
        result = await cur.fetchone()
        return result[0]


async def set_vk_nickname(vk_id, nickname):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        try:
            await cur.execute('INSERT INTO VkNickName (vk_id, nickname) VALUES (?, ?)', (vk_id, nickname))
        except aiosqlite.IntegrityError:
            await cur.execute(
                'UPDATE VkNickName SET nickname=? where vk_id=?',
                (nickname, vk_id)
            )
        await db.commit()


async def get_vk_nickname(vk_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT nickname FROM VkNickName where vk_id=?',
            (vk_id,)
        )
        result = await cur.fetchone()
        if result:
            return result[0]


async def set_discord_nickname(discord_id, nickname):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        try:
            await cur.execute(
                'INSERT INTO DiscordNickName (discord_id, nickname) VALUES (?, ?)',
                (discord_id, nickname)
            )
        except aiosqlite.IntegrityError:
            await cur.execute(
                'UPDATE DiscordNickName SET nickname=? where discord_id=?',
                (nickname, discord_id)
            )
        await db.commit()


async def get_discord_nickname(discord_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT nickname FROM DiscordNickName where discord_id=?',
            (discord_id,)
        )
        result = await cur.fetchone()
        if result:
            return result[0]


async def create_gallery(images_urls):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()

        await cur.execute(
            'SELECT max(gallery_id) FROM GalleryToImage'
        )

        result = await cur.fetchone()
        if result[0] is None:
            gallery_id = 0
        else:
            gallery_id = result[0] + 1

        for image_url in images_urls:
            await cur.execute(
                'INSERT INTO GalleryToImage (gallery_id, image_url) VALUES (?, ?)',
                (gallery_id, image_url)
            )
        await db.commit()

        return gallery_id


async def get_gallery_images(gallery_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT image_url FROM GalleryToImage WHERE gallery_id=? ORDER BY rowid',
            (gallery_id,)
        )
        result = await cur.fetchall()
        images = [row[0] for row in result]
        return images


async def save_message(server_id, channel_id, chat_id,
                       vk_message_id, discord_message_id):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'INSERT INTO MessageToMessage'
            '(server_id, channel_id, chat_id,'
            'vk_message_id, discord_message_id)'
            'VALUES'
            '(:server_id, :channel_id, :chat_id,'
            ':vk_message_id, :discord_message_id)',
            (server_id, channel_id, chat_id,
             vk_message_id, discord_message_id)
        )
        await db.commit()


async def get_vk_message(discord_message: discord.Message):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'SELECT chat_id, vk_message_id FROM MessageToMessage'
            'WHERE server_id = :server_id'
            'and channel_id = :channel_id'
            'and discord_message_od = :discord_message_id',
            (
                discord_message.guild.id,
                discord_message.channel.id,
                discord_message.id)
        )
        result = await cur.fetchone()
        return result
