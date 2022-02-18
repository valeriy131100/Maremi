from functools import wraps
from typing import Callable

from disnake.ext import commands

from .optional_arg import optional_arg_decorator


class ContentMessageContext(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content_message = None

    async def load_content_message(self):
        message = self.message
        if ref := message.reference:
            self.content_message = (
                await message.channel.fetch_message(ref.message_id)
            )
        else:
            self.content_message = message

    async def custom_delete(self, delay=0):
        message = self.message
        await message.delete(delay=delay)
        if message.reference:
            await self.content_message.delete()


@optional_arg_decorator
def use_content_message_context(func: Callable, *,
                                custom_context: ContentMessageContext = (
                                         ContentMessageContext
                                 )):
    @wraps(func)
    async def wrapper(obj, context: commands.Context, *args, **kwargs):
        new_context: ContentMessageContext = await context.bot.get_context(
            context.message,
            cls=custom_context
        )
        await new_context.load_content_message()
        await func(obj, new_context, *args, **kwargs)

    return wrapper


class NotFoundRef(Exception):
    def __init__(self, message):
        self.message = message


@optional_arg_decorator
def prefetch_ref(func: Callable, raise_not_found=True):
    @wraps(func)
    async def wrapper(obj, context: commands.Context, *args, **kwargs):
        channel = context.channel
        ref = context.message.reference

        if ref:
            context.ref_message = await channel.fetch_message(ref.message_id)
        elif raise_not_found:
            raise NotFoundRef(context.message)

        await func(obj, context, *args, **kwargs)

    return wrapper
