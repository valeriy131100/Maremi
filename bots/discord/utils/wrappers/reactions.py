from functools import wraps
from typing import Callable, Optional

from disnake.ext import commands

from .optional_arg import optional_arg_decorator

SUCCESS_EMOJI = '✅'
FAILURE_EMOJI = '❌'
WTF_EMOJI = '❗'
LOADING_EMOJI = '⌛'


@optional_arg_decorator
def react_success_and_delete(func: Callable, *,
                             exception: Optional[Exception] = None,
                             exceptions: Optional[tuple] = tuple(),
                             delete_delay: int = 5,
                             success_delete_delay: Optional[int] = None):
    @wraps(func)
    async def wrapper(obj, context: commands.Context, *args, **kwargs):
        message = context.message
        excepted = exception if exception else exceptions
        success = False
        _delete_delay = delete_delay

        try:
            await func(obj, context, *args, **kwargs)
        except excepted:
            await message.add_reaction(FAILURE_EMOJI)
        except Exception as unhandled_exception:
            await message.add_reaction(WTF_EMOJI)
            raise unhandled_exception
        else:
            await message.add_reaction(SUCCESS_EMOJI)
            success = True
            if success_delete_delay is not None:
                _delete_delay = success_delete_delay
        finally:
            if hasattr(context, 'custom_delete') and success:
                await context.custom_delete(delay=_delete_delay)
            else:
                await message.delete(delay=_delete_delay)

    return wrapper


def react_loading(func: Callable):
    @wraps(func)
    async def wrapper(obj, context: commands.Context, *args, **kwargs):
        message = context.message

        await message.add_reaction(LOADING_EMOJI)

        try:
            await func(obj, context, *args, **kwargs)
        finally:
            await message.remove_reaction(
                LOADING_EMOJI,
                member=context.bot.user
            )

    return wrapper
