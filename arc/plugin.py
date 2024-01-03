from __future__ import annotations

import typing as t

from arc.abc.plugin import PluginBase
from arc.internal.sigparse import parse_event_signature
from arc.internal.types import EventCallbackT, EventT, GatewayClientT, RESTClientT

if t.TYPE_CHECKING:
    import hikari

__all__ = ("RESTPluginBase", "GatewayPluginBase")

P = t.ParamSpec("P")
T = t.TypeVar("T")


class RESTPluginBase(PluginBase[RESTClientT]):
    """The default implementation of a REST plugin.
    To use this with the default [`RESTClient`][arc.client.RESTClient] implementation, see [`RESTPlugin`][arc.client.RESTPlugin].

    Parameters
    ----------
    name : str
        The name of this plugin. This must be unique across all plugins.

    Usage
    -----
    ```py
    plugin = arc.RESTPlugin("MyPlugin")

    @plugin.include
    @arc.slash_command("ping", "Ping the bot.")
    async def ping(ctx: arc.RESTContext) -> None:
        ...

    # Snip

    client.add_plugin(plugin)
    ```
    """

    @property
    def is_rest(self) -> bool:
        return True


class GatewayPluginBase(PluginBase[GatewayClientT]):
    """The default implementation of a gateway plugin.
    To use this with the default [`GatewayClient`][arc.client.GatewayClient] implementation, see [`GatewayPlugin`][arc.client.GatewayPlugin].

    Parameters
    ----------
    name : str
        The name of this plugin. This must be unique across all plugins.

    Usage
    -----
    ```py
    plugin = arc.GatewayPlugin("MyPlugin")

    @plugin.include
    @arc.slash_command("ping", "Ping the bot.")
    async def ping(ctx: arc.GatewayContext) -> None:
        ...

    # Snip

    client.add_plugin(plugin)
    ```
    """

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._listeners: dict[type[hikari.Event], set[EventCallbackT[t.Any]]] = {}

    @property
    def is_rest(self) -> bool:
        return False

    @property
    def listeners(self) -> t.Mapping[type[hikari.Event], t.Collection[EventCallbackT[t.Any]]]:
        return self._listeners

    def subscribe(self, event: type[hikari.Event], callback: EventCallbackT[t.Any]) -> None:
        """Subscribe to an event.

        Parameters
        ----------
        event : type[hikari.Event]
            The event to subscribe to.
        callback : Callable[[EventT], Awaitable[None]]
            The callback to call when the event is dispatched.
        """
        if event not in self.listeners:
            self._listeners[event] = set()

        self._listeners[event].add(callback)

        if self._client is not None:
            self._client.subscribe(event, callback)

    def unsubscribe(self, event: type[hikari.Event], callback: EventCallbackT[t.Any]) -> None:
        """Unsubscribe from an event.

        Parameters
        ----------
        event : type[hikari.Event]
            The event to unsubscribe from.
        callback : Callable[[EventT], Awaitable[None]]
            The callback to unsubscribe.
        """
        if event not in self.listeners:
            return

        self._listeners[event].remove(callback)

        if self._client is not None:
            self._client.unsubscribe(event, callback)

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
        t.Callable[[EventT], EventT]
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

    def _client_include_hook(self, client: GatewayClientT) -> None:
        super()._client_include_hook(client)

        for event, callbacks in self.listeners.items():
            for callback in callbacks:
                client.subscribe(event, callback)

    def _client_remove_hook(self) -> None:
        if self._client is None:
            raise RuntimeError(f"Plugin '{self.name}' is not included in a client.")

        for event, callbacks in self.listeners.items():
            for callback in callbacks:
                self.client.unsubscribe(event, callback)

        super()._client_remove_hook()


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
