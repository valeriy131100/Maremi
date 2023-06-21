from typing import TYPE_CHECKING

from disnake import ApplicationCommandInteraction as BaseCommandInteraction, Client as BaseClient
from disnake.ext.commands import Bot as BaseBot
from disnake.state import ConnectionState as BaseConnectionState
if TYPE_CHECKING:
    from disnake.types.gateway import InteractionCreateEvent
    from disnake.types.interactions import ApplicationCommandInteraction as ApplicationCommandInteractionPayload

from models import Server


class CommandInteraction(BaseCommandInteraction):
    def __init__(self, *, data: "ApplicationCommandInteractionPayload", state: BaseConnectionState) -> None:
        super().__init__(data=data, state=state)

        self.db_server: None | Server = None

    async def load_db_server(self) -> None:
        self.db_server = await Server.get_or_none(server_id=self.guild_id)

    async def ephemeral(self, *args, **kwargs) -> None:
        return await self.send(*args, **kwargs, ephemeral=True)


class ConnectionState(BaseConnectionState):
    def parse_interaction_create(self, data: "InteractionCreateEvent") -> None:
        if data["type"] == 2:
            interaction = CommandInteraction(data=data, state=self)
            self.dispatch("application_command", interaction)
            self.dispatch("interaction", interaction)
            return

        return super().parse_interaction_create(data)


class Client(BaseClient):
    def _get_state(self, **kwargs) -> ConnectionState:
        return ConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            **kwargs
        )


class Bot(BaseBot, Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
