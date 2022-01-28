import types
from collections.abc import Iterable
from typing import Union

from tortoise.exceptions import DoesNotExist
from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule

import config
from models import Server, ServerChannelAlias


def is_callable(obj):
    return isinstance(
        obj,
        (
            types.FunctionType,
            types.BuiltinFunctionType,
            types.MethodType,
            types.BuiltinMethodType
        )
    )


class StartsWithRule(ABCRule):
    def __init__(self, command_getter, prefix=None, return_text=True):
        self.command_getter = command_getter
        self.prefix = prefix if prefix else config.vk_prefix
        self.return_text = return_text

    def get_return_type(self, text):
        if self.return_text:
            return {
                'cleared_text': text
            }
        else:
            return True

    async def check(self, event: Message) -> Union[dict, bool]:
        command_getter = self.command_getter
        prefix = self.prefix
        if isinstance(command_getter, str):
            commands = [command_getter]
        elif isinstance(command_getter, Iterable):
            commands = command_getter
        elif is_callable(command_getter):
            commands = command_getter()
        else:
            return False

        for command in commands:
            if event.text.startswith(f'{prefix}{command} '):
                result_text = event.text.replace(
                    f'{prefix}{command} ', '', 1
                )
                return self.get_return_type(result_text)
            elif event.text == f'{prefix}{command}':
                return self.get_return_type('')
        else:
            return False


class AliasRule(ABCRule):
    def __init__(self, prefix=None, return_text=True):
        self.prefix = prefix if prefix else config.vk_alias_prefix
        self.return_text = return_text

    def get_return_type(self, text, alias):
        if self.return_text:
            return {
                'cleared_text': text,
                'alias': alias
            }
        else:
            return True

    async def check(self, event: Message) -> Union[dict, bool]:
        prefix = self.prefix
        try:
            server = await Server.get(chat_id=event.chat_id)
        except DoesNotExist:
            return False

        commands = ServerChannelAlias.filter(server=server)
        if not commands:
            return False

        commands = await commands.values_list('alias', flat=True)

        for command in commands:
            if event.text.startswith(f'{prefix}{command} '):
                result_text = event.text.replace(
                    f'{prefix}{command} ', '', 1
                )
                return self.get_return_type(result_text, command)
            elif event.text == f'{prefix}{command}':
                return self.get_return_type('', command)
        else:
            return False


class NotStartsWithRule(ABCRule):
    def __init__(self, prefixes=None):
        self.prefixes = prefixes if prefixes else (
            config.vk_prefix,
            config.vk_alias_prefix
        )

    async def check(self, event: Message) -> Union[dict, bool]:
        if not event.text.startswith(self.prefixes):
            return True
        else:
            return False

