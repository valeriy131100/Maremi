import re
from collections.abc import Iterable
from typing import Union, re as re_types

from tortoise.exceptions import DoesNotExist
from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule

import config
from models import Server, ServerChannelAlias


COMPILED_RULES = {}


def get_rule(pattern: str) -> re_types.Pattern:
    compiled = COMPILED_RULES.get(pattern)

    if compiled is None:
        compiled = re.compile(pattern, re.I)
        COMPILED_RULES[compiled] = compiled

    return compiled


class StartsWithRule(ABCRule):
    def __init__(self, commands_getter, prefix=None, return_text=True):
        self.commands_getter = commands_getter
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
        command_getter = self.commands_getter
        prefix = self.prefix
        if isinstance(command_getter, str):
            commands = [command_getter]
        elif isinstance(command_getter, Iterable):
            commands = command_getter
        elif callable(command_getter):
            commands = command_getter()
        else:
            return False

        for command in commands:
            pattern = get_rule(f'^{prefix}{command}')
            if pattern.match(event.text):
                result_text = pattern.sub('', event.text)
                return self.get_return_type(result_text.lstrip())
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
            pattern = get_rule(f'^{prefix}{command}')
            if pattern.match(event.text):
                result_text = pattern.sub('', event.text)
                return self.get_return_type(result_text.lstrip(), command)
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

