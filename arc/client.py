from __future__ import annotations

import logging
import typing as t

import hikari

from arc.abc.client import Client
from arc.context import Context
from arc.errors import NoResponseIssuedError
from arc.events import CommandErrorEvent, StartedEvent, StoppingEvent
from arc.internal.sigparse import parse_event_signature
from arc.internal.types import GatewayBotT, RESTBotT
from arc.plugin import GatewayPluginBase, RESTPluginBase

if t.TYPE_CHECKING:
    import alluka
    import typing_extensions as te

    from arc import AutodeferMode

    from .internal.types import EventCallbackT, EventT, ResponseBuilderT

__all__ = (
    "GatewayClientBase",
    "RESTClientBase",
    "GatewayClient",
    "RESTClient",
    "GatewayContext",
    "RESTContext",
    "RESTPlugin",
    "GatewayPlugin",
)


T = t.TypeVar("T")
P = t.ParamSpec("P")

logger = logging.getLogger(__name__)


class GatewayClientBase(Client[GatewayBotT]):
    """The base class for an arc client with Gateway support.
    This class primarily exists to allow for the creation of custom client types.

    For the default implementation of a Gateway client, see [`GatewayClient`][arc.client.GatewayClient].

    Parameters
    ----------
    app : hikari.GatewayBotAware
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflakeish] | None
        The guilds that commands will be registered in by default
    autosync : bool
        Whether to automatically sync commands on startup
    autodefer : bool | AutodeferMode
        Whether to automatically defer responses
        This applies to all commands, and can be overridden on a per-command basis.
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for commands
        This applies to all commands, and can be overridden on a per-command basis.
    is_nsfw : bool
        Whether commands are NSFW
        This applies to all commands, and can be overridden on a per-command basis.
    is_dm_enabled : bool
        Whether commands are enabled in DMs
        This applies to all commands, and can be overridden on a per-command basis.
    provided_locales : t.Sequence[hikari.Locale] | None
        The locales that will be provided to the client by locale provider callbacks
    injector : alluka.Client | None
        If you already have an injector instance, you may pass it here.
        Otherwise, a new one will be created by default.
    """

    __slots__: t.Sequence[str] = ()

    def __init__(
        self,
        app: GatewayBotT,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflakeish | hikari.PartialGuild]
        | hikari.UndefinedType = hikari.UNDEFINED,
        autosync: bool = True,
        autodefer: bool | AutodeferMode = True,
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        is_nsfw: bool = False,
        is_dm_enabled: bool = True,
        provided_locales: t.Sequence[hikari.Locale] | None = None,
        injector: alluka.abc.Client | None = None,
    ) -> None:
        super().__init__(
            app,
            default_enabled_guilds=default_enabled_guilds,
            autosync=autosync,
            autodefer=autodefer,
            default_permissions=default_permissions,
            is_nsfw=is_nsfw,
            is_dm_enabled=is_dm_enabled,
            provided_locales=provided_locales,
            injector=injector,
        )
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
        await self.app.event_manager.dispatch(StartedEvent(self))

    async def _on_gatewaybot_shutdown(self, event: hikari.StoppingEvent) -> None:
        await self._on_shutdown()
        await self.app.event_manager.dispatch(StoppingEvent(self))

    async def _on_gatewaybot_interaction_create(self, event: hikari.InteractionCreateEvent) -> None:
        if isinstance(event.interaction, hikari.CommandInteraction):
            await self.on_command_interaction(event.interaction)
        elif isinstance(event.interaction, hikari.AutocompleteInteraction):
            await self.on_autocomplete_interaction(event.interaction)

    async def _on_error(self, ctx: Context[te.Self], exception: Exception) -> None:
        if not self.app.event_manager.get_listeners(CommandErrorEvent):
            return await super()._on_error(ctx, exception)

        self.app.event_manager.dispatch(CommandErrorEvent(self, ctx, exception))

    def subscribe(self, event_type: type[EventT], callback: EventCallbackT[EventT]) -> None:
        """Subscribe to an event.

        Parameters
        ----------
        event_type : type[EventT]
            The event type to subscribe to.

            `EventT` must be a subclass of `hikari.events.base_events.Event`.
        callback : t.Callable[EventT], t.Awaitable[None]]
            The callback to call when the event is dispatched.
        """
        self.app.event_manager.subscribe(event_type, callback)  # pyright: ignore reportGeneralTypeIssues

    def unsubscribe(self, event_type: type[EventT], callback: EventCallbackT[EventT]) -> None:
        """Unsubscribe from an event.

        Parameters
        ----------
        event_type : type[EventT]
            The event type to unsubscribe from.
        callback : t.Callable[[EventT], t.Awaitable[None]]
            The callback to unsubscribe.
        """
        self.app.event_manager.unsubscribe(event_type, callback)  # pyright: ignore reportGeneralTypeIssues

    def listen(self, *event_types: type[EventT]) -> t.Callable[[EventCallbackT[EventT]], EventCallbackT[EventT]]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        *event_types : type[EventT]
            The event types to subscribe to. If not provided, the event type will be inferred
            instead from the type hints on the function signature.

            `EventT` must be a subclass of `hikari.events.base_events.Event`.

        Returns
        -------
        t.Callable[t.Callable[[EventT], t.Awaitable[None]]], t.Callable[[EventT], t.Awaitable[None]]]
            A decorator for a coroutine function that passes it to
            `EventManager.subscribe` before returning the function
            reference.
        """

        def decorator(func: EventCallbackT[EventT]) -> EventCallbackT[EventT]:
            types = event_types or parse_event_signature(func)

            for event_type in types:
                self.subscribe(event_type, func)

            return func

        return decorator


class RESTClientBase(Client[RESTBotT]):
    """The base class for an arc client with REST support.
    This class primarily exists to allow for the creation of custom client types.

    For the default implementation of a REST client, see [`RESTClient`][arc.client.RESTClient].

    !!! warning
        The client will take over the `hikari.CommandInteraction` and `hikari.AutocompleteInteraction` listeners of the passed bot.

    Parameters
    ----------
    app : hikari.GatewayBotAware
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflakeish | hikari.PartialGuild] | None
        The guilds that commands will be registered in by default
    autosync : bool
        Whether to automatically sync commands on startup
    autodefer : bool | AutodeferMode
        Whether to automatically defer responses
        This applies to all commands, and can be overridden on a per-command basis.
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for commands
        This applies to all commands, and can be overridden on a per-command basis.
    is_nsfw : bool
        Whether commands are NSFW
        This applies to all commands, and can be overridden on a per-command basis.
    is_dm_enabled : bool
        Whether commands are enabled in DMs
        This applies to all commands, and can be overridden on a per-command basis.
    provided_locales : t.Sequence[hikari.Locale] | None
        The locales that will be provided to the client by locale provider callbacks
    injector : alluka.abc.Client | None
        If you already have an injector instance, you may pass it here.
        Otherwise, a new one will be created by default.
    """

    __slots__: t.Sequence[str] = ()

    def __init__(
        self,
        app: RESTBotT,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflakeish | hikari.PartialGuild]
        | hikari.UndefinedType = hikari.UNDEFINED,
        autosync: bool = True,
        autodefer: bool | AutodeferMode = True,
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        is_nsfw: bool = False,
        is_dm_enabled: bool = True,
        provided_locales: t.Sequence[hikari.Locale] | None = None,
        injector: alluka.abc.Client | None = None,
    ) -> None:
        super().__init__(
            app,
            default_enabled_guilds=default_enabled_guilds,
            autosync=autosync,
            autodefer=autodefer,
            default_permissions=default_permissions,
            is_nsfw=is_nsfw,
            is_dm_enabled=is_dm_enabled,
            provided_locales=provided_locales,
            injector=injector,
        )
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


# These two are classes for DI reasons, they should not ever contain any code.
class GatewayClient(GatewayClientBase[hikari.GatewayBotAware]):
    """The default gateway client implementation. Effectively an alias for [`arc.GatewayClientBase[hikari.GatewayBotAware]`][arc.client.GatewayClientBase].

    If you want to use a RESTBot, use [`RESTClient`][arc.client.RESTClient] instead.

    Parameters
    ----------
    app : hikari.GatewayBotAware
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflakeish] | None
        The guilds that commands will be registered in by default
    autosync : bool
        Whether to automatically sync commands on startup
    autodefer : bool | AutodeferMode
        Whether to automatically defer responses
        This applies to all commands, and can be overridden on a per-command basis.
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for commands
        This applies to all commands, and can be overridden on a per-command basis.
    is_nsfw : bool
        Whether commands are NSFW
        This applies to all commands, and can be overridden on a per-command basis.
    is_dm_enabled : bool
        Whether commands are enabled in DMs
        This applies to all commands, and can be overridden on a per-command basis.
    provided_locales : t.Sequence[hikari.Locale] | None
        The locales that will be provided to the client by locale provider callbacks
    injector : alluka.abc.Client | None
        If you already have an injector instance, you may pass it here.
        Otherwise, a new one will be created by default.

    Examples
    --------
    ```py
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)
    ```
    """

    __slots__: t.Sequence[str] = ()


class RESTClient(RESTClientBase[hikari.RESTBotAware]):
    """The default REST client implementation. Effectively an alias for [`arc.RESTClientBase[hikari.RESTBotAware]`][arc.client.RESTClientBase].

    If you want to use GatewayBot, use [`GatewayClient`][arc.client.GatewayClient] instead.

    Parameters
    ----------
    app : hikari.GatewayBotAware
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflakeish | hikari.PartialGuild] | None
        The guilds that commands will be registered in by default
    autosync : bool
        Whether to automatically sync commands on startup
    autodefer : bool | AutodeferMode
        Whether to automatically defer responses
        This applies to all commands, and can be overridden on a per-command basis.
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for commands
        This applies to all commands, and can be overridden on a per-command basis.
    is_nsfw : bool
        Whether commands are NSFW
        This applies to all commands, and can be overridden on a per-command basis.
    is_dm_enabled : bool
        Whether commands are enabled in DMs
        This applies to all commands, and can be overridden on a per-command basis.
    provided_locales : t.Sequence[hikari.Locale] | None
        The locales that will be provided to the client by locale provider callbacks
    injector : alluka.abc.Client | None
        If you already have an injector instance, you may pass it here.
        Otherwise, a new one will be created by default.


    Examples
    --------
    ```py
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)
    ```

    !!! warning
        The client will take over the `hikari.CommandInteraction` and `hikari.AutocompleteInteraction` listeners of the passed bot.
    """

    __slots__: t.Sequence[str] = ()


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
