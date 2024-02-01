from __future__ import annotations

import asyncio
import contextlib
import typing as t

from arc.abc.concurrency_limiting import ConcurrencyLimiterProto
from arc.context.base import Context
from arc.internal.types import ClientT

__all__ = (
    "ConcurrencyLimiter",
    "CommandConcurrencyLimiter",
    "global_concurrency",
    "guild_concurrency",
    "channel_concurrency",
    "user_concurrency",
    "member_concurrency",
    "custom_concurrency",
)

KeyT = t.TypeVar("KeyT")


# This is cursed
class _BoundedSemaphore(asyncio.BoundedSemaphore):
    @property
    def value(self) -> int:
        return self._value


class _Bucket(t.Generic[KeyT]):
    """Handles the concurrency limiting of a single item. (E.g. a single user or a channel)."""

    __slots__ = ("_key", "_max_concurrent", "_semaphore", "_limiter")

    def __init__(self, key: str, max_concurrent: int, limiter: ConcurrencyLimiter[KeyT]) -> None:
        self._key = key
        self._max_concurrent = max_concurrent
        self._semaphore = _BoundedSemaphore(max_concurrent)
        self._limiter = limiter

    @property
    def key(self) -> str:
        """The key of the bucket."""
        return self._key

    @property
    def remaining(self) -> int:
        """The amount of requests remaining until the bucket is exhausted."""
        return self._semaphore.value

    @property
    def semaphore(self) -> _BoundedSemaphore:
        """The semaphore of the bucket."""
        return self._semaphore

    @classmethod
    def for_limiter(cls, key: str, limiter: ConcurrencyLimiter[KeyT]) -> _Bucket[KeyT]:
        """Create a new bucket for a ConcurrencyLimiter."""
        return cls(key=key, max_concurrent=limiter._capacity, limiter=limiter)

    @property
    def is_exhausted(self) -> bool:
        """Return a boolean determining if the bucket is exhausted."""
        return self._semaphore.locked()

    @property
    def is_stale(self) -> bool:
        """Return a boolean determining if the bucket is stale.
        If a bucket is stale, it is no longer in use and can be purged.
        """
        return self._semaphore.value == self._max_concurrent


class _ConcurrencyLimiterContextManager(t.Generic[KeyT]):
    __slots__ = ("_limiter", "_item")

    def __init__(self, limiter: ConcurrencyLimiter[KeyT], item: KeyT) -> None:
        self._limiter = limiter
        self._item = item

    async def __aenter__(self) -> None:
        await self._limiter.acquire(self._item)

    async def __aexit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        self._limiter.release(self._item)


class ConcurrencyLimiter(t.Generic[KeyT]):
    """A general purpose concurrency limiter.
    Accepts a key extraction function and allocates buckets for each unique key.

    Example:
    ```py
    limiter = arc.utils.ConcurrencyLimiter[int](
        capacity=5,
        get_key_with=lambda x: str(x),
    )

    async with limiter(69):
        print("69 is now being processed")
    ```

    !!! note
        For use with commands, see [`CommandConcurrencyLimiter`][arc.utils.concurrency_limiter.CommandConcurrencyLimiter].

    Parameters
    ----------
    capacity : int
        The maximum amount of concurrently running requests.
    get_key_with : t.Callable[[KeyT], str]
        A callable that returns a key for the concurrency limiter bucket.

    See Also
    --------
    - [`CommandConcurrencyLimiter`][arc.utils.concurrency_limiter.CommandConcurrencyLimiter]
    - [`guild_concurrency()`][arc.utils.concurrency_limiter.guild_concurrency]
    - [`channel_concurrency()`][arc.utils.concurrency_limiter.channel_concurrency]
    - [`user_concurrency()`][arc.utils.concurrency_limiter.user_concurrency]
    - [`member_concurrency()`][arc.utils.concurrency_limiter.member_concurrency]
    - [`custom_concurrency()`][arc.utils.concurrency_limiter.custom_concurrency]
    """

    __slots__: t.Sequence[str] = ("_capacity", "_buckets", "_get_key")

    def __init__(self, capacity: int, *, get_key_with: t.Callable[[KeyT], str]) -> None:
        self._capacity = capacity
        self._buckets: dict[str, _Bucket[KeyT]] = {}
        self._get_key = get_key_with

    def __call__(self, item: KeyT) -> _ConcurrencyLimiterContextManager[KeyT]:
        """Use the limiter as a context manager.

        This will acquire a concurrency slot for an item and release it when the context exits.

        Example:
        ```py
        limiter = arc.utils.ConcurrencyLimiter[str](5, lambda x: x)

        async with limiter("foo"):
            print("foo is now being processed")
        ```

        This is equivalent to:
        ```py
        limiter = arc.utils.ConcurrencyLimiter[str](5, lambda x: x)

        try:
            await limiter.acquire("foo")
            print("foo is now being processed")
        finally:
            await limiter.release("foo")
        ```
        """
        return _ConcurrencyLimiterContextManager(self, item)

    @property
    def limit(self) -> int:
        """The maximum amount of concurrently running requests."""
        return self._capacity

    async def acquire(self, item: KeyT) -> None:
        """Acquire a concurrency slot for an item.

        This will block until a slot is available.
        """
        key = self._get_key(item)
        bucket = self._buckets.setdefault(key, _Bucket.for_limiter(key, self))
        await bucket.semaphore.acquire()

    def release(self, item: KeyT) -> None:
        """Release a concurrency slot for an item."""
        key = self._get_key(item)
        bucket = self._buckets.get(key)
        if bucket is None:
            raise ValueError("Key not found in limiter")

        with contextlib.suppress(ValueError):
            bucket.semaphore.release()

        if bucket.is_stale:
            del self._buckets[key]

    def is_exhausted(self, item: KeyT) -> bool:
        """Return a boolean determining if the limiter is exhausted for an item."""
        key = self._get_key(item)
        bucket = self._buckets.get(key)
        if bucket is None:
            return False
        return bucket.is_exhausted


class CommandConcurrencyLimiter(ConcurrencyLimiter[Context[ClientT]], ConcurrencyLimiterProto[ClientT]):
    """A concurrency limiter specialized for use with `arc` commands.
    This limiter only accepts `arc.context.Context` instances as keys.

    For a generic implementation that works with any key type,
    see [`ConcurrencyLimiter`][arc.utils.concurrency_limiter.ConcurrencyLimiter].

    Parameters
    ----------
    capacity : int
        The maximum amount of concurrently running command instances.
    get_key_with : t.Callable[[Context[ClientT]], str]
        A callable that returns a key for the concurrency limiter bucket.

    See Also
    --------
    - [`guild_concurrency()`][arc.utils.concurrency_limiter.guild_concurrency]
    - [`channel_concurrency()`][arc.utils.concurrency_limiter.channel_concurrency]
    - [`user_concurrency()`][arc.utils.concurrency_limiter.user_concurrency]
    - [`member_concurrency()`][arc.utils.concurrency_limiter.member_concurrency]
    - [`custom_concurrency()`][arc.utils.concurrency_limiter.custom_concurrency]
    """

    __slots__ = ()

    def __call__(self, item: Context[ClientT]) -> _ConcurrencyLimiterContextManager[Context[ClientT]]:
        """Use the limiter as a context manager.

        This will acquire a concurrency slot for an item and release it when the context exits.

        Example:
        ```py
        limiter = arc.utils.CommandConcurrencyLimiter(5, lambda ctx: str(ctx.guild_id)))

        async with limiter(ctx):
            print("ctx is now being processed")
        ```

        This is equivalent to:
        ```py
        limiter = arc.utils.CommandConcurrencyLimiter(5, lambda ctx: str(ctx.guild_id)))

        try:
            await limiter.acquire(ctx)
            print("ctx is now being processed")
        finally:
            await limiter.release(ctx)
        ```
        """
        return super().__call__(item)


def global_concurrency(limit: int) -> CommandConcurrencyLimiter[t.Any]:
    """Limit a command to a certain amount of concurrent instances globally.

    Parameters
    ----------
    limit : int
        The maximum amount of concurrently running command instances.

    Returns
    -------
    CommandConcurrencyLimiter[t.Any]
        A concurrency limiter for use with a command.

    Examples
    --------
    ```py
    @arc.with_concurrency_limit(arc.global_concurrency(1))
    ```
    """
    return CommandConcurrencyLimiter(limit, get_key_with=lambda _: "amongus")


def guild_concurrency(limit: int) -> CommandConcurrencyLimiter[t.Any]:
    """Limit a command to a certain amount of concurrent instances per guild.

    Parameters
    ----------
    limit : int
        The maximum amount of concurrently running command instances.

    Returns
    -------
    CommandConcurrencyLimiter[t.Any]
        A concurrency limiter for use with a command.

    Examples
    --------
    ```py
    @arc.with_concurrency_limit(arc.guild_concurrency(1))
    ```
    """
    return CommandConcurrencyLimiter(limit, get_key_with=lambda ctx: str(ctx.guild_id))


def channel_concurrency(limit: int) -> CommandConcurrencyLimiter[t.Any]:
    """Limit a command to a certain amount of concurrent instances per channel.

    Parameters
    ----------
    limit : int
        The maximum amount of concurrently running command instances.

    Returns
    -------
    CommandConcurrencyLimiter[t.Any]
        A concurrency limiter for use with a command.

    Examples
    --------
    ```py
    @arc.with_concurrency_limit(arc.channel_concurrency(1))
    ```
    """
    return CommandConcurrencyLimiter(limit, get_key_with=lambda ctx: str(ctx.channel_id))


def user_concurrency(limit: int) -> CommandConcurrencyLimiter[t.Any]:
    """Limit a command to a certain amount of concurrent instances per user.

    Parameters
    ----------
    limit : int
        The maximum amount of concurrently running command instances.

    Returns
    -------
    CommandConcurrencyLimiter[t.Any]
        A concurrency limiter for use with a command.

    Examples
    --------
    ```py
    @arc.with_concurrency_limit(arc.user_concurrency(1))
    ```
    """
    return CommandConcurrencyLimiter(limit, get_key_with=lambda ctx: str(ctx.author.id))


def member_concurrency(limit: int) -> CommandConcurrencyLimiter[t.Any]:
    """Limit a command to a certain amount of concurrent instances per member.

    Parameters
    ----------
    limit : int
        The maximum amount of concurrently running command instances.

    Returns
    -------
    CommandConcurrencyLimiter[t.Any]
        A concurrency limiter for use with a command.

    Examples
    --------
    ```py
    @arc.with_concurrency_limit(arc.member_concurrency(1))
    ```
    """
    return CommandConcurrencyLimiter(limit, get_key_with=lambda ctx: f"{ctx.guild_id}:{ctx.author.id}")


def custom_concurrency(
    limit: int, get_key_with: t.Callable[[Context[ClientT]], str]
) -> CommandConcurrencyLimiter[t.Any]:
    """Limit a command to a certain amount of concurrent instances per custom key.

    Parameters
    ----------
    limit : int
        The maximum amount of concurrently running command instances.
    get_key_with : t.Callable[[Context[ClientT]], str]
        A callable that returns a key for the concurrency limiter bucket.

    Returns
    -------
    CommandConcurrencyLimiter[t.Any]
        A concurrency limiter for use with a command.

    Examples
    --------
    ```py
    # This is identical to 'arc.guild_concurrency(1)'
    @arc.with_concurrency_limit(arc.custom_concurrency(1, lambda ctx: str(ctx.guild_id)))
    ```
    """
    return CommandConcurrencyLimiter(limit, get_key_with=get_key_with)


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
