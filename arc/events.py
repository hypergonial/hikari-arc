from __future__ import annotations

import typing as t

import hikari

from arc.internal.types import GatewayClientT

if t.TYPE_CHECKING:
    from arc.context import Context

__all__ = ("ArcEvent", "CommandErrorEvent", "StartedEvent", "StoppingEvent")


class ArcEvent(hikari.Event):
    """Base class for all Arc events."""

    __slots__: t.Sequence[str] = ()


class StartedEvent(ArcEvent, t.Generic[GatewayClientT]):
    """Event dispatched when the client has started.

    This is notably different from hikari's `StartedEvent`
    because it fires after all command syncing was completed and the client has finished its startup process.
    """

    __slots__: t.Sequence[str] = ("_client",)

    def __init__(self, client: GatewayClientT) -> None:
        self._client = client

    @property
    def client(self) -> GatewayClientT:
        """The client instance that started."""
        return self._client

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self._client.app


class StoppingEvent(ArcEvent, t.Generic[GatewayClientT]):
    """Event dispatched when the client is stopping.

    This event is fired after the shutdown hook has been processed.
    """

    __slots__: t.Sequence[str] = ("_client",)

    def __init__(self, client: GatewayClientT) -> None:
        self._client = client

    @property
    def client(self) -> GatewayClientT:
        """The client instance that is stopping."""
        return self._client

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self._client.app


class CommandErrorEvent(ArcEvent, t.Generic[GatewayClientT]):
    """Event dispatched when a command raises an exception that is not handled by any error handlers.

    !!! warning
        Creating any listeners for this event will disable the client error handler completely.
    """

    __slots__: t.Sequence[str] = ("_client", "_context", "_exception")

    def __init__(self, client: GatewayClientT, context: Context[GatewayClientT], exception: Exception) -> None:
        self._context = context
        self._client = client
        self._exception = exception

    @property
    def client(self) -> GatewayClientT:
        """The client instance that raised the exception."""
        return self._client

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self._client.app

    @property
    def context(self) -> Context[GatewayClientT]:
        """The invocation context that raised the exception."""
        return self._context

    @property
    def exception(self) -> Exception:
        """The exception that was raised."""
        return self._exception
