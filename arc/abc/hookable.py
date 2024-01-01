from __future__ import annotations

import abc
import typing as t

from arc.internal.types import ClientT, HookableT, HookT, PostHookT

if t.TYPE_CHECKING:
    import typing_extensions as te


class HookResult:
    """The result of a hook.

    Parameters
    ----------
    abort : bool
        Whether to abort the execution of the command.
        If True, the command execution will be silently aborted.
        If this is undesired, you should raise an exception instead.
    """

    def __init__(self, abort: bool = False) -> None:
        self._abort = abort


class Hookable(abc.ABC, t.Generic[ClientT]):
    """An interface for objects that can have hooks set on them."""

    @property
    @abc.abstractmethod
    def hooks(self) -> t.MutableSequence[HookT[ClientT]]:
        """The pre-execution hooks for this object."""

    @property
    @abc.abstractmethod
    def post_hooks(self) -> t.MutableSequence[PostHookT[ClientT]]:
        """The post-execution hooks for this object."""

    def _resolve_hooks(self) -> list[HookT[ClientT]]:
        """Resolve all pre-execution hooks that apply to this object."""
        ...

    def _resolve_post_hooks(self) -> list[PostHookT[ClientT]]:
        """Resolve all post-execution hooks that apply to this object."""
        ...

    def add_hook(self, hook: HookT[ClientT]) -> te.Self:
        """Add a new pre-execution hook to this object.

        Any function that takes a [Context][`arc.context.base.Context`] as its sole parameter
        and returns either a [`HookResult`][arc.abc.hookable.HookResult] or
        `None` can be used as a hook.

        Parameters
        ----------
        hook : HookT[ClientT]
            The hook to add.

        Returns
        -------
        te.Self
            This object for chaining.
        """
        self.hooks.append(hook)
        return self

    def add_post_hook(self, hook: PostHookT[ClientT]) -> te.Self:
        """Add a new post-execution hook to this object.

        Any function that takes a [Context][`arc.context.base.Context`] as its sole parameter
        and returns either a [`HookResult`][arc.abc.hookable.HookResult] or
        `None` can be used as a hook.

        Parameters
        ----------
        hook : PostHookT[ClientT]
            The post-execution hook to add.

        Returns
        -------
        te.Self
            This object for chaining.
        """
        self.post_hooks.append(hook)
        return self


def with_hook(hook: HookT[ClientT]) -> t.Callable[[HookableT], HookableT]:
    """Add a new pre-execution hook to a hookable object. It will run before the command callback.

    Any function that takes a [Context][`arc.context.base.Context`] as its sole parameter
    and returns either a [`HookResult`][arc.abc.hookable.HookResult] or
    `None` can be used as a hook.

    Usage
    -----
    ```py
    @client.include
    @arc.with_hook(arc.guild_only) # Add a pre-execution hook to a command
    @arc.slash_command("foo", "Foo command description")
    async def foo(ctx: arc.GatewayContext) -> None:
        ...
    ```
    """

    def decorator(hookable: HookableT) -> HookableT:
        hookable.hooks.append(hook)
        return hookable

    return decorator


def with_post_hook(hook: PostHookT[ClientT]) -> t.Callable[[HookableT], HookableT]:
    """Add a new post-execution hook to a hookable object. It will run after the command callback.

    Any function that takes a [Context][`arc.context.base.Context`] as its sole parameter
    and returns either a [`HookResult`][arc.abc.hookable.HookResult] or
    `None` can be used as a hook.

    Post-execution hooks are not executed if a pre-execution hook aborts the execution of the command.

    !!! warning
        Post-execution hooks **are** called even if the command callback raises an exception.
        You can see if the command callback failed by checking [`Context.has_command_failed`][arc.context.base.Context.has_command_failed].

    Usage
    -----
    ```py
    @client.include
    @arc.with_post_hook(arc.guild_only) # Add a post-execution hook to a command
    @arc.slash_command("foo", "Foo command description")
    async def foo(ctx: arc.GatewayContext) -> None:
        ...
    ```
    """

    def decorator(hookable: HookableT) -> HookableT:
        hookable.post_hooks.append(hook)
        return hookable

    return decorator
