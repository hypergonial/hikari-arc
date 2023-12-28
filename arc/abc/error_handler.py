from __future__ import annotations

import abc
import typing as t

import attr

from ..internal.types import ClientT, ErrorHandlerCallbackT

if t.TYPE_CHECKING:
    from ..context import Context


@attr.define(slots=False)
class HasErrorHandler(abc.ABC, t.Generic[ClientT]):
    _error_handler: ErrorHandlerCallbackT[ClientT] | None = attr.field(default=None, init=False)

    @property
    def error_handler(self) -> t.Optional[ErrorHandlerCallbackT[ClientT]]:
        return self._error_handler

    def set_error_handler(self, callback: ErrorHandlerCallbackT[ClientT]) -> ErrorHandlerCallbackT[ClientT]:
        """Decorator to set an error handler for this object. This can be added to commands, groups, or plugins.

        This function will be called when an exception is raised during the invocation of a command.

        Usage
        -----
        ```py
        @client.include
        @arc.slash_command("foo", "Foo command description")
        async def foo(ctx: arc.Context[ClientT]) -> None:
            raise Exception("foo")

        @foo.set_error_handler
        async def foo_error_handler(ctx: arc.Context[ClientT], exc: Exception) -> None:
            await ctx.respond("foo failed")
        ```
        """
        self._error_handler = callback
        return callback

    @abc.abstractmethod
    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        ...
