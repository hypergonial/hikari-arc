from __future__ import annotations

import abc
import typing as t

from arc.internal.types import ClientT, HasConcurrencyLimiterT

if t.TYPE_CHECKING:
    import typing_extensions as te

    from arc.context.base import Context

KeyT = t.TypeVar("KeyT", contravariant=True)


@t.runtime_checkable
class ConcurrencyLimiterProto(t.Protocol[ClientT]):
    """A protocol for valid concurrency limiters that `arc` can use.

    !!! tip
        An easy (but not necessary) way to ensure you've implemented all methods
        is to inherit from this protocol.
    """

    @property
    @abc.abstractmethod
    def limit(self) -> int:
        """The limit of the concurrency limiter."""

    @abc.abstractmethod
    async def acquire(self, ctx: Context[ClientT], /) -> None:
        """Acquire a concurrency slot for a context.

        This should block until a slot is available.
        """

    @abc.abstractmethod
    def release(self, ctx: Context[ClientT], /) -> None:
        """Release a concurrency slot for a context."""

    @abc.abstractmethod
    def is_exhausted(self, ctx: Context[ClientT], /) -> bool:
        """Return whether the concurrency limiter is exhausted for a context."""


class HasConcurrencyLimiter(abc.ABC, t.Generic[ClientT]):
    """A trait for objects that can have a concurrency limiter."""

    __slots__: t.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """The concurrency limiter for this object."""

    @concurrency_limiter.setter
    @abc.abstractmethod
    def concurrency_limiter(self, limiter: ConcurrencyLimiterProto[ClientT] | None) -> None:
        """Set the concurrency limiter for this object."""

    @abc.abstractmethod
    def _resolve_concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """Resolve the concurrency limiter for this object."""

    def set_concurrency_limiter(self, limiter: ConcurrencyLimiterProto[ClientT]) -> te.Self:
        """Set the concurrency limiter for this object."""
        self.concurrency_limiter = limiter
        return self


def with_concurrency_limit(
    limiter: ConcurrencyLimiterProto[ClientT],
) -> t.Callable[[HasConcurrencyLimiterT], HasConcurrencyLimiterT]:
    """A decorator that sets a concurrency limiter for an object.

    !!! note
        An object can only have one concurrency limiter set at a time.

    Parameters
    ----------
    limiter : ConcurrencyLimiterProto[ClientT]
        The concurrency limiter to use.

    Returns
    -------
    t.Callable[[HasConcurrencyLimiterT], HasConcurrencyLimiterT]
        The object with the concurrency limiter set.

    Examples
    --------
    ```py
    @client.include
    # Max 5 users can use this command at a time.
    @arc.with_concurrency_limit(arc.user_concurrency(5))
    @arc.slash_command(...)
    async def foo(ctx: arc.GatewayContext) -> None:
        ...
    ```

    See Also
    --------
    - [`guild_concurrency()`][arc.utils.concurrency_limiter.guild_concurrency]
    - [`channel_concurrency()`][arc.utils.concurrency_limiter.channel_concurrency]
    - [`user_concurrency()`][arc.utils.concurrency_limiter.user_concurrency]
    - [`member_concurrency()`][arc.utils.concurrency_limiter.member_concurrency]
    - [`custom_concurrency()`][arc.utils.concurrency_limiter.custom_concurrency]
    """

    def decorator(func: HasConcurrencyLimiterT) -> HasConcurrencyLimiterT:
        func.set_concurrency_limiter(limiter)
        return func

    return decorator


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
