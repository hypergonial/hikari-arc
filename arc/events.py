from __future__ import annotations

import typing as t

import hikari

from .internal.types import GatewayClientT

if t.TYPE_CHECKING:
    from .context import Context

__all__ = ("ArcEvent", "CommandErrorEvent")


class ArcEvent(hikari.Event):
    """Base class for all Arc events."""

    pass


class CommandErrorEvent(ArcEvent, t.Generic[GatewayClientT]):
    """Event dispatched when a command raises an exception that is not handled by any error handlers."""

    def __init__(self, client: GatewayClientT, context: Context[GatewayClientT], exception: Exception) -> None:
        self._context = context
        self._client = client
        self._exception = exception

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
