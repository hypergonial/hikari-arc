from __future__ import annotations

import abc
import typing as t

from arc.internal.types import ClientT

if t.TYPE_CHECKING:
    from arc.abc.hookable import HookResult
    from arc.context.base import Context


@t.runtime_checkable
class LimiterProto(t.Protocol, t.Generic[ClientT]):
    """A protocol that all limiter hooks should implement.
    A limiter is simply a special type of hook with added methods.

    If you're looking to integrate your own ratelimiter implementation,
    you should make sure to implement all methods defined here.

    !!! tip
        An easy (but not necessary) way to ensure you've implemented all methods
        is to inherit from this protocol.
    """

    @abc.abstractmethod
    async def __call__(self, ctx: Context[ClientT], /) -> HookResult:
        """Call the limiter with the given context.
        Implementations should raise an exception if the limiter is ratelimited
        or abort via [`HookResult`][arc.abc.hookable.HookResult].

        Parameters
        ----------
        ctx : Context
            The context to evaluate the ratelimit under.
        """

    @abc.abstractmethod
    def reset(self, ctx: Context[ClientT], /) -> None:
        """Reset the limiter for the given context.

        Parameters
        ----------
        ctx : Context
            The context to reset the ratelimit for.
        """

    @abc.abstractmethod
    def is_rate_limited(self, ctx: Context[ClientT], /) -> bool:
        """Check if the limiter is rate limited for the given context.

        Parameters
        ----------
        ctx : Context
            The context to evaluate the ratelimit under.

        Returns
        -------
        bool
            Whether or not the limiter is ratelimited.
        """
