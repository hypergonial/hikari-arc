from __future__ import annotations

import abc
import typing as t

from arc.internal.types import ClientT, ErrorHandlerCallbackT

if t.TYPE_CHECKING:
    from ..context import Context


class HasErrorHandler(abc.ABC, t.Generic[ClientT]):
    """An interface for objects that can have an error handler set on them."""

    @property
    @abc.abstractmethod
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this object."""

    def set_error_handler(self, callback: ErrorHandlerCallbackT[ClientT]) -> ErrorHandlerCallbackT[ClientT]:
        """Decorator to set an error handler for this object. This can be added to commands, groups, or plugins.

        This function will be called when an exception is raised during the invocation of a command.

        Usage
        -----
        ```py
        @client.include
        @arc.slash_command("foo", "Foo command description")
        async def foo(ctx: arc.GatewayContext) -> None:
            raise Exception("foo")

        @foo.set_error_handler
        async def foo_error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
            await ctx.respond("foo failed")
        ```
        """
        self._error_handler = callback
        return callback

    @abc.abstractmethod
    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        """Handle an exception or propagate it to the next error handler if it cannot be handled."""
