from __future__ import annotations

import abc
import typing as t

from arc.internal.types import ClientT, ErrorHandlerCallbackT

if t.TYPE_CHECKING:
    from ..context import Context


class HasErrorHandler(abc.ABC, t.Generic[ClientT]):
    """A trait for objects that can have an error handler set on them."""

    __slots__: t.Sequence[str] = ()

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

        Examples
        --------
        ```py
        @client.include
        @arc.slash_command("foo", "Foo command description")
        async def foo(ctx: arc.GatewayContext) -> None:
            raise RuntimeError("foo")

        @foo.set_error_handler
        async def foo_error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
            if isinstance(exc, RuntimeError):
                await ctx.respond("foo failed")
                return

            raise exc
        ```

        !!! warning
            Errors that cannot be handled by the error handler should be re-raised.
            Otherwise they will not propagate to the next error handler.
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
