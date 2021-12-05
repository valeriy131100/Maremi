import aiosqlite
import aiofiles
from config import db_file


async def create_db():
    async with aiosqlite.connect(db_file) as db, aiofiles.open('createdb.sql', 'r') as create_sql:
        cur = await db.cursor()
        await cur.executescript(await create_sql.read())


async def make_server_to_chat(server_id, chat_id, default_channel):
    async with aiosqlite.connect(db_file) as db:
        cur = await db.cursor()
        await cur.execute(
            'INSERT INTO Server (server_id, server_default_channel) VALUES (?, ?)',
            (server_id, default_channel)
        )
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
        server_id = (await cur.fetchone())[0]
        return server_id


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
