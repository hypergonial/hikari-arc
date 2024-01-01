from __future__ import annotations

import typing as t

from arc.abc.plugin import PluginBase
from arc.internal.types import EventCallbackT, GatewayClientT, RESTClientT

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
        self._listeners: dict[t.Type[hikari.Event], set[EventCallbackT[t.Any]]] = {}

    @property
    def is_rest(self) -> bool:
        return False

    @property
    def listeners(self) -> t.Mapping[t.Type[hikari.Event], t.Collection[EventCallbackT[t.Any]]]:
        return self._listeners

    def _client_include_hook(self, client: GatewayClientT) -> None:
        super()._client_include_hook(client)

        for event, callbacks in self.listeners.items():
            for callback in callbacks:
                client.app.event_manager.subscribe(event, callback)

    def _client_remove_hook(self) -> None:
        if self._client is None:
            raise RuntimeError(f"Plugin '{self.name}' is not included in a client.")

        for event, callbacks in self.listeners.items():
            for callback in callbacks:
                self.client.app.event_manager.unsubscribe(event, callback)

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
