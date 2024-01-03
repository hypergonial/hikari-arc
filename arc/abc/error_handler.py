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

    @error_handler.setter
    @abc.abstractmethod
    def error_handler(self, callback: ErrorHandlerCallbackT[ClientT] | None) -> None:
        """Set the error handler for this object."""

    @t.overload
    def set_error_handler(
        self, callback: None = ...
    ) -> t.Callable[[ErrorHandlerCallbackT[ClientT]], ErrorHandlerCallbackT[ClientT]]:
        ...

    @t.overload
    def set_error_handler(self, callback: ErrorHandlerCallbackT[ClientT]) -> ErrorHandlerCallbackT[ClientT]:
        ...

    def set_error_handler(
        self, callback: ErrorHandlerCallbackT[ClientT] | None = None
    ) -> ErrorHandlerCallbackT[ClientT] | t.Callable[[ErrorHandlerCallbackT[ClientT]], ErrorHandlerCallbackT[ClientT]]:
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

        def decorator(func: ErrorHandlerCallbackT[ClientT]) -> ErrorHandlerCallbackT[ClientT]:
            self.error_handler = func
            return func

        if callback is not None:
            return decorator(callback)

        return decorator

    @abc.abstractmethod
    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        """Handle an exception or propagate it to the next error handler if it cannot be handled."""
