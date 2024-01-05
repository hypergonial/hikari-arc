from __future__ import annotations

import asyncio
import sys
import time
import traceback
import typing as t
from collections import deque

import attr

from arc.abc.hookable import HookResult
from arc.abc.limiter import LimiterProto
from arc.errors import UnderCooldownError
from arc.internal.types import ClientT

if t.TYPE_CHECKING:
    from arc.context.base import Context

__all__ = (
    "RateLimiter",
    "global_limiter",
    "guild_limiter",
    "channel_limiter",
    "user_limiter",
    "member_limiter",
    "custom_limiter",
)


@attr.define(slots=True)
class _Quota(t.Generic[ClientT]):
    """Handles the ratelimiting of a single item. (E.g. a single user or a channel)."""

    reset_at: float
    """The time at which the quota resets."""
    remaining: int
    """The amount of requests remaining until the quota is exhausted."""
    bucket: RateLimiter[ClientT]
    """The limiter this quota belongs to."""
    queue: deque[asyncio.Event] = attr.field(factory=deque)
    """A list of events to set as the iter task proceeds."""
    task: asyncio.Task[None] | None = attr.field(default=None)
    """The task that is currently iterating over the queue."""

    @classmethod
    def for_limiter(cls, limiter: RateLimiter[ClientT]) -> _Quota[ClientT]:
        """Create a new Quota for a RateLimiter."""
        return cls(bucket=limiter, reset_at=time.monotonic() + limiter.period, remaining=limiter.limit)

    def start_queue(self) -> None:
        """Start the queue of a Quota.
        This will start setting events in the queue until the bucket is ratelimited.
        """
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._iter_queue())

    def reset(self) -> None:
        """Reset the ratelimit."""
        self.remaining = self.bucket.limit
        self.reset_at = time.monotonic() + self.bucket.period

    async def _iter_queue(self) -> None:
        """Iterate over the queue and set events until exhausted."""
        try:
            if self.remaining <= 0 and self.reset_at > time.monotonic():
                # Sleep until ratelimit expires
                sleep_time = self.reset_at - time.monotonic()
                await asyncio.sleep(sleep_time)
                self.reset()
            elif self.reset_at <= time.monotonic():
                self.reset()

            # Set events while not ratelimited
            while self.remaining > 0 and self.queue:
                self.remaining -= 1
                self.queue.popleft().set()

            self.task = None

        except Exception as e:
            print(f"Task Exception was never retrieved: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)


class RateLimiter(LimiterProto[ClientT]):
    """The default implementation of a ratelimiter.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    get_key_with : Callable[[Context[t.Any]], str]
        A callable that returns a key for the ratelimiter bucket.
    """

    __slots__ = ("period", "limit", "_quotas", "_get_key")

    def __init__(self, period: float, limit: int, *, get_key_with: t.Callable[[Context[t.Any]], str]) -> None:
        self.period: float = period
        self.limit: int = limit
        self._quotas: t.Dict[str, _Quota[ClientT]] = {}
        self._get_key: t.Callable[[Context[t.Any]], str] = get_key_with

    def get_key(self, ctx: Context[t.Any]) -> str:
        """Get key for ratelimiter bucket."""
        return self._get_key(ctx)

    def is_rate_limited(self, ctx: Context[t.Any]) -> bool:
        """Returns a boolean determining if the ratelimiter is ratelimited or not.

        Parameters
        ----------
        ctx : Context[t.Any]
            The context to evaluate the ratelimit under.

        Returns
        -------
        bool
            A boolean determining if the ratelimiter is ratelimited or not.
        """
        now = time.monotonic()

        if data := self._quotas.get(self.get_key(ctx)):
            if data.reset_at <= now:
                return False
            return data.remaining <= 0
        return False

    async def acquire(self, ctx: Context[t.Any], *, wait: bool = True) -> None:
        """Acquire a quota, block execution if ratelimited and wait is True.

        Parameters
        ----------
        ctx : Context[t.Any]
            The context to evaluate the ratelimit under.
        wait : bool
            Determines if this call should block in
            case of hitting a ratelimit.

        Raises
        ------
        UnderCooldownError
            If the ratelimiter is ratelimited and wait is False.
        """
        event = asyncio.Event()

        # Get existing or insert new quota
        quota = self._quotas.setdefault(self.get_key(ctx), _Quota.for_limiter(self))
        quota.queue.append(event)
        quota.start_queue()

        if wait:
            await event.wait()
        elif self.is_rate_limited(ctx):
            retry_after = quota.reset_at - time.monotonic()
            raise UnderCooldownError(self, retry_after, f"Ratelimited for {retry_after} seconds.")

    async def __call__(self, ctx: Context[t.Any]) -> HookResult:
        """Acquire a ratelimit, fail if ratelimited.

        Parameters
        ----------
        ctx : Context[t.Any]
            The context to evaluate the ratelimit under.

        Returns
        -------
        HookResult
            A hook result to conform to the limiter protocol.

        Raises
        ------
        UnderCooldownError
            If the ratelimiter is ratelimited.
        """
        await self.acquire(ctx, wait=False)
        return HookResult()

    def reset(self, ctx: Context[t.Any]) -> None:
        """Reset the ratelimit for a given context."""
        if quota := self._quotas.get(self.get_key(ctx)):
            quota.reset()


def global_limiter(period: float, limit: int) -> RateLimiter[t.Any]:
    """Create a global ratelimiter.

    This ratelimiter is shared across all invocation contexts.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    """
    return RateLimiter(period, limit, get_key_with=lambda _: "amongus")


def guild_limiter(period: float, limit: int) -> RateLimiter[t.Any]:
    """Create a guild ratelimiter.

    This ratelimiter is shared across all contexts in a guild.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    """
    return RateLimiter(period, limit, get_key_with=lambda ctx: str(ctx.guild_id))


def channel_limiter(period: float, limit: int) -> RateLimiter[t.Any]:
    """Create a channel ratelimiter.

    This ratelimiter is shared across all contexts in a channel.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    """
    return RateLimiter(period, limit, get_key_with=lambda ctx: str(ctx.channel_id))


def user_limiter(period: float, limit: int) -> RateLimiter[t.Any]:
    """Create a user ratelimiter.

    This ratelimiter is shared across all contexts by a user.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    """
    return RateLimiter(period, limit, get_key_with=lambda ctx: str(ctx.author.id))


def member_limiter(period: float, limit: int) -> RateLimiter[t.Any]:
    """Create a member ratelimiter.

    This ratelimiter is shared across all contexts by a member in a guild.
    The same user in a different guild will be assigned a different quota.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    """
    return RateLimiter(period, limit, get_key_with=lambda ctx: f"{ctx.author.id}:{ctx.guild_id}")


def custom_limiter(period: float, limit: int, get_key_with: t.Callable[[Context[t.Any]], str]) -> RateLimiter[t.Any]:
    """Create a custom ratelimiter.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the quota resets.
    limit : int
        The amount of requests allowed in a quota.
    get_key_with : Callable[[Context[t.Any]], str]
        A callable that returns a key for the ratelimiter bucket.
        This key is used to identify the bucket.
    """
    return RateLimiter(period, limit, get_key_with=get_key_with)


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
