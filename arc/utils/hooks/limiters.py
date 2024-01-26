from __future__ import annotations

import typing as t

from arc.abc.limiter import LimiterProto
from arc.context.base import Context
from arc.errors import UnderCooldownError
from arc.internal.types import ClientT
from arc.utils.ratelimiter import RateLimiter, RateLimiterExhaustedError

__all__ = (
    "LimiterHook",
    "global_limiter",
    "guild_limiter",
    "channel_limiter",
    "user_limiter",
    "member_limiter",
    "custom_limiter",
)


class LimiterHook(RateLimiter[Context[ClientT]], LimiterProto[ClientT]):
    """The default implementation of a ratelimiter that can be used as a hook.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.
    get_key_with : t.Callable[[Context[t.Any]], str]
        A callable that returns a key for the ratelimiter bucket.

    See Also
    --------
    - [`global_limiter`][arc.utils.hooks.limiters.global_limiter]
    - [`guild_limiter`][arc.utils.hooks.limiters.guild_limiter]
    - [`channel_limiter`][arc.utils.hooks.limiters.channel_limiter]
    - [`user_limiter`][arc.utils.hooks.limiters.user_limiter]
    - [`member_limiter`][arc.utils.hooks.limiters.member_limiter]
    - [`custom_limiter`][arc.utils.hooks.limiters.custom_limiter]
    """

    async def acquire(self, ctx: Context[ClientT], /, *, wait: bool = True) -> None:
        """Acquire a bucket, block execution if ratelimited and wait is True.

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
        try:
            return await super().acquire(ctx, wait=wait)
        except RateLimiterExhaustedError as exc:
            raise UnderCooldownError(
                self, exc.retry_after, f"Command is under cooldown for '{exc.retry_after}' seconds."
            ) from exc


def global_limiter(period: float, limit: int) -> LimiterHook[t.Any]:
    """Create a global ratelimiter.

    This ratelimiter is shared across all invocation contexts.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.

    Raises
    ------
    RateLimiterExhaustedError
        If the limiter is exhausted.

    Examples
    --------
    ```py
    @arc.with_hook(arc.global_limiter(5.0, 1))
    ```
    """
    return LimiterHook(period, limit, get_key_with=lambda _: "amongus")


def guild_limiter(period: float, limit: int) -> LimiterHook[t.Any]:
    """Create a guild ratelimiter.

    This ratelimiter is shared across all contexts in a guild.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.

    Raises
    ------
    RateLimiterExhaustedError
        If the limiter is exhausted.

    Examples
    --------
    ```py
    @arc.with_hook(arc.guild_limiter(5.0, 1))
    ```
    """
    return LimiterHook(period, limit, get_key_with=lambda ctx: str(ctx.guild_id))


def channel_limiter(period: float, limit: int) -> LimiterHook[t.Any]:
    """Create a channel ratelimiter.

    This ratelimiter is shared across all contexts in a channel.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.

    Raises
    ------
    RateLimiterExhaustedError
        If the limiter is exhausted.

    Examples
    --------
    ```py
    @arc.with_hook(arc.channel_limiter(5.0, 1))
    ```
    """
    return LimiterHook(period, limit, get_key_with=lambda ctx: str(ctx.channel_id))


def user_limiter(period: float, limit: int) -> LimiterHook[t.Any]:
    """Create a user ratelimiter.

    This ratelimiter is shared across all contexts by a user.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.

    Raises
    ------
    RateLimiterExhaustedError
        If the limiter is exhausted.

    Examples
    --------
    ```py
    @arc.with_hook(arc.user_limiter(5.0, 1))
    ```
    """
    return LimiterHook(period, limit, get_key_with=lambda ctx: str(ctx.author.id))


def member_limiter(period: float, limit: int) -> LimiterHook[t.Any]:
    """Create a member ratelimiter.

    This ratelimiter is shared across all contexts by a member in a guild.
    The same user in a different guild will be assigned a different bucket.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.

    Raises
    ------
    RateLimiterExhaustedError
        If the limiter is exhausted.

    Examples
    --------
    ```py
    @arc.with_hook(arc.member_limiter(5.0, 1))
    ```
    """
    return LimiterHook(period, limit, get_key_with=lambda ctx: f"{ctx.author.id}:{ctx.guild_id}")


def custom_limiter(period: float, limit: int, get_key_with: t.Callable[[Context[t.Any]], str]) -> LimiterHook[t.Any]:
    """Create a ratelimiter with a custom key extraction function.

    Parameters
    ----------
    period : float
        The period, in seconds, after which the bucket resets.
    limit : int
        The amount of requests allowed in a bucket.
    get_key_with : t.Callable[[Context[t.Any]], str]
        A callable that returns a key for the ratelimiter bucket. This key is used to identify the bucket.
        For instance, to create a ratelimiter that is shared across all contexts in a guild,
        you would use `lambda ctx: str(ctx.guild_id)`.

    Raises
    ------
    RateLimiterExhaustedError
        If the limiter is exhausted.

    Examples
    --------
    ```py
    # This is identical to 'arc.guild_limiter(5.0, 1)'
    @arc.with_hook(arc.custom_limiter(5.0, 1, lambda ctx: str(ctx.guild_id)))
    ```
    """
    return LimiterHook(period, limit, get_key_with=get_key_with)


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
