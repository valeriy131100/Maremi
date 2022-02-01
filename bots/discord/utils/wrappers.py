from functools import wraps
from typing import Callable, Optional

from disnake.ext import commands

SUCCESS_EMOJI = '✅'
FAILURE_EMOJI = '❌'
WTF_EMOJI = '❗'


def optional_arg_decorator(decorator):
    def wrapped_decorator(*args, **kwargs):
        if len(args) == 1:
            return decorator(args[0])

        else:
            def real_decorator(function):
                return decorator(function, *args, **kwargs)

            return real_decorator

    return wrapped_decorator


@optional_arg_decorator
def react_and_delete(func: Callable, *,
                     exception: Optional[Exception] = None,
                     exceptions: Optional[tuple] = tuple()):
    @wraps(func)
    async def wrapper(cls, context: commands.Context, *args, **kwargs):
        message = context.message
        excepted = exception if exception else exceptions

        try:
            await func(cls, context, *args, **kwargs)
        except excepted:
            await message.add_reaction(FAILURE_EMOJI)
        except Exception as unhandled_exception:
            await message.add_reaction(WTF_EMOJI)
            raise unhandled_exception
        else:
            await message.add_reaction(SUCCESS_EMOJI)
        finally:
            await message.delete(delay=5)

    return wrapper
