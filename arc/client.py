from __future__ import annotations

import logging
import typing as t

import hikari

from arc.abc.client import Client
from arc.context import Context
from arc.errors import NoResponseIssuedError
from arc.events import CommandErrorEvent
from arc.plugin import GatewayPluginBase, RESTPluginBase

if t.TYPE_CHECKING:
    import typing_extensions as te

    from .internal.types import EventCallbackT, EventT, ResponseBuilderT

__all__ = ("GatewayClient", "RESTClient")


T = t.TypeVar("T")
P = t.ParamSpec("P")

logger = logging.getLogger(__name__)


class GatewayClient(Client[hikari.GatewayBotAware]):
    """The default implementation for an arc client with `hikari.GatewayBotAware` support.
    If you want to use a `hikari.RESTBotAware`, use [`RESTClient`][arc.client.RESTClient] instead.

    Parameters
    ----------
    app : hikari.GatewayBotAware
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | None, optional
        The guilds that slash commands will be registered in by default, by default None
    autosync : bool, optional
        Whether to automatically sync commands on startup, by default True

    Usage
    -----
    ```py
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)

    ...
    ```
    """

    __slots__: t.Sequence[str] = ()

    def __init__(
        self,
        app: hikari.GatewayBotAware,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflake] | None = None,
        autosync: bool = True,
    ) -> None:
        super().__init__(app, default_enabled_guilds=default_enabled_guilds, autosync=autosync)
        self.app.event_manager.subscribe(hikari.StartedEvent, self._on_gatewaybot_startup)
        self.app.event_manager.subscribe(hikari.StoppingEvent, self._on_gatewaybot_shutdown)
        self.app.event_manager.subscribe(hikari.InteractionCreateEvent, self._on_gatewaybot_interaction_create)

    @property
    def is_rest(self) -> bool:
        """Whether this client is a REST client."""
        return False

    @property
    def cache(self) -> hikari.api.Cache:
        """The cache for this client."""
        return self.app.cache

    async def _on_gatewaybot_startup(self, event: hikari.StartedEvent) -> None:
        await self._on_startup()

    async def _on_gatewaybot_shutdown(self, event: hikari.StoppingEvent) -> None:
        await self._on_shutdown()

    async def _on_gatewaybot_interaction_create(self, event: hikari.InteractionCreateEvent) -> None:
        if isinstance(event.interaction, hikari.CommandInteraction):
            await self.on_command_interaction(event.interaction)
        elif isinstance(event.interaction, hikari.AutocompleteInteraction):
            await self.on_autocomplete_interaction(event.interaction)

    async def _on_error(self, ctx: Context[te.Self], exception: Exception) -> None:
        if not self.app.event_manager.get_listeners(CommandErrorEvent):
            return await super()._on_error(ctx, exception)

        self.app.event_manager.dispatch(CommandErrorEvent(self, ctx, exception))

    def listen(self, *event_types: t.Type[EventT]) -> t.Callable[[EventCallbackT[EventT]], EventCallbackT[EventT]]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        *event_types : t.Type[EventT] | None
            The event types to subscribe to. The implementation may allow this
            to be undefined. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

            `EventT` must be a subclass of `hikari.events.base_events.Event`.

        Returns
        -------
        t.Callable[[EventT], EventT]
            A decorator for a coroutine function that passes it to
            `EventManager.subscribe` before returning the function
            reference.
        """
        return self.app.event_manager.listen(*event_types)


class RESTClient(Client[hikari.RESTBotAware]):
    """The default implementation for an arc client with `hikari.RESTBotAware` support.
    If you want to use `hikari.GatewayBotAware`, use [`GatewayClient`][arc.client.GatewayClient] instead.

    Parameters
    ----------
    app : hikari.RESTBotAware
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | None, optional
        The guilds that slash commands will be registered in by default, by default None
    autosync : bool, optional
        Whether to automatically sync commands on startup, by default True


    Usage
    -----
    ```py
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)

    ...
    ```

    !!! warning
        The client will take over the `hikari.CommandInteraction` and `hikari.AutocompleteInteraction` listeners of the passed bot.
    """

    __slots__: t.Sequence[str] = ()

    def __init__(
        self,
        app: hikari.RESTBotAware,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflake] | None = None,
        autosync: bool = True,
    ) -> None:
        super().__init__(app, default_enabled_guilds=default_enabled_guilds, autosync=autosync)
        self.app.add_startup_callback(self._on_restbot_startup)
        self.app.add_shutdown_callback(self._on_restbot_shutdown)
        self.app.interaction_server.set_listener(
            hikari.CommandInteraction, self._on_restbot_interaction_create, replace=True
        )
        self.app.interaction_server.set_listener(
            hikari.AutocompleteInteraction, self._on_restbot_autocomplete_interaction_create, replace=True
        )

    @property
    def is_rest(self) -> bool:
        """Whether this client is a REST client."""
        return True

    async def _on_restbot_startup(self, bot: hikari.RESTBotAware) -> None:
        await self._on_startup()
        await self.on_restbot_startup(bot)

    async def on_restbot_startup(self, bot: hikari.RESTBotAware) -> None:
        """A function that is called when the client is started.

        Parameters
        ----------
        bot : hikari.RESTBotAware
            The bot that was started.
        """

    async def _on_restbot_shutdown(self, bot: hikari.RESTBotAware) -> None:
        await self._on_shutdown()
        await self.on_restbot_shutdown(bot)

    async def on_restbot_shutdown(self, bot: hikari.RESTBotAware) -> None:
        """A function that is called when the client is shut down.

        Parameters
        ----------
        bot : hikari.RESTBotAware
            The bot that was shut down.
        """

    async def _on_restbot_interaction_create(self, interaction: hikari.CommandInteraction) -> ResponseBuilderT:
        builder = await self.on_command_interaction(interaction)
        if builder is None:
            raise NoResponseIssuedError(
                f"No response was issued to interaction for command: {interaction.command_name} ({interaction.command_type})."
            )
        return builder

    async def _on_restbot_autocomplete_interaction_create(
        self, interaction: hikari.AutocompleteInteraction
    ) -> hikari.api.InteractionAutocompleteBuilder:
        builder = await self.on_autocomplete_interaction(interaction)
        if builder is None:
            raise NoResponseIssuedError(
                f"No response was issued to autocomplete request for command: {interaction.command_name} ({interaction.command_type})."
            )
        return builder


GatewayContext = Context[GatewayClient]
"""A context using the default gateway client implementation. An alias for [`arc.Context[arc.GatewayClient]`][arc.context.base.Context]."""

RESTContext = Context[RESTClient]
"""A context using the default REST client implementation. An alias for [`arc.Context[arc.RESTClient]`][arc.context.base.Context]."""

RESTPlugin = RESTPluginBase[RESTClient]
"""A plugin using the default REST client implementation. An alias for [`arc.RESTPluginBase[arc.RESTClient]`][arc.plugin.RESTPluginBase]."""

GatewayPlugin = GatewayPluginBase[GatewayClient]
"""An alias for [`arc.GatewayPluginBase[arc.GatewayClient]`][arc.plugin.GatewayPluginBase]."""

# MIT License
#
# Copyright (c) 2023-present hypergonial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
