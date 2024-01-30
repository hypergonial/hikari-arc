from __future__ import annotations

import abc
import functools
import inspect
import itertools
import typing as t

import hikari

from arc.abc.command import CallableCommandBase, _CommandSettings
from arc.abc.concurrency_limiting import ConcurrencyLimiterProto, HasConcurrencyLimiter
from arc.abc.error_handler import HasErrorHandler
from arc.abc.hookable import Hookable
from arc.command import MessageCommand, SlashCommand, SlashGroup, UserCommand
from arc.command.slash import SlashSubCommand, SlashSubGroup
from arc.context import AutodeferMode, Context
from arc.internal.types import BuilderT, ClientT, ErrorHandlerCallbackT, HookT, PostHookT, SlashCommandLike

if t.TYPE_CHECKING:
    from arc.abc.command import CommandBase

__all__ = ("PluginBase",)

P = t.ParamSpec("P")
T = t.TypeVar("T")


class PluginBase(HasErrorHandler[ClientT], Hookable[ClientT], HasConcurrencyLimiter[ClientT]):
    """An abstract base class for plugins.

    !!! note
        Parameters left as `hikari.UNDEFINED` will be inherited from the parent client.

    Parameters
    ----------
    name : str
        The name of this plugin. This must be unique across all plugins.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | hikari.UndefinedType
        The default guilds to enable commands in
    autodefer : bool | AutodeferMode
        If True, all commands in this plugin will automatically defer if it is taking longer than 2 seconds to respond.
        This can be overridden on a per-command basis.
    is_dm_enabled : bool | hikari.UndefinedType
        Whether commands in this plugin are enabled in DMs
        This can be overridden on a per-command basis.
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for this plugin
        This can be overridden on a per-command basis.
    is_nsfw : bool | hikari.UndefinedType
        Whether this plugin is only usable in NSFW channels
    """

    __slots__: t.Sequence[str] = (
        "_client",
        "_name",
        "_default_enabled_guilds",
        "_cmd_settings",
        "_slash_commands",
        "_user_commands",
        "_message_commands",
        "_error_handler",
        "_hooks",
        "_post_hooks",
        "_concurrency_limiter",
    )

    def __init__(
        self,
        name: str,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflakeish | hikari.PartialGuild]
        | hikari.UndefinedType = hikari.UNDEFINED,
        autodefer: bool | AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED,
        is_dm_enabled: bool | hikari.UndefinedType = hikari.UNDEFINED,
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        is_nsfw: bool | hikari.UndefinedType = hikari.UNDEFINED,
    ) -> None:
        self._client: ClientT | None = None
        self._name = name
        self._default_enabled_guilds = (
            tuple(hikari.Snowflake(i) for i in default_enabled_guilds)
            if default_enabled_guilds is not hikari.UNDEFINED
            else hikari.UNDEFINED
        )
        self._cmd_settings = _CommandSettings(
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            is_dm_enabled=is_dm_enabled,
            default_permissions=default_permissions,
            is_nsfw=is_nsfw,
        )

        self._slash_commands: dict[str, SlashCommandLike[ClientT]] = {}
        self._user_commands: dict[str, UserCommand[ClientT]] = {}
        self._message_commands: dict[str, MessageCommand[ClientT]] = {}
        self._error_handler: ErrorHandlerCallbackT[ClientT] | None = None
        self._hooks: list[HookT[ClientT]] = []
        self._post_hooks: list[PostHookT[ClientT]] = []
        self._concurrency_limiter: ConcurrencyLimiterProto[ClientT] | None = None

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this plugin."""
        return self._error_handler

    @error_handler.setter
    def error_handler(self, callback: ErrorHandlerCallbackT[ClientT] | None) -> None:
        """Set the error handler for this plugin."""
        self._error_handler = callback

    @property
    def concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """The concurrency limiter for this plugin."""
        return self._concurrency_limiter

    @concurrency_limiter.setter
    def concurrency_limiter(self, limiter: ConcurrencyLimiterProto[ClientT] | None) -> None:
        """Set the concurrency limiter for this plugin."""
        self._concurrency_limiter = limiter

    @property
    def hooks(self) -> t.MutableSequence[HookT[ClientT]]:
        """The pre-execution hooks for this plugin."""
        return self._hooks

    @property
    def post_hooks(self) -> t.MutableSequence[PostHookT[ClientT]]:
        """The post-execution hooks for this plugin."""
        return self._post_hooks

    @property
    @abc.abstractmethod
    def is_rest(self) -> bool:
        """Whether or not this plugin is a REST plugin."""

    @property
    def name(self) -> str:
        """The name of this plugin."""
        return self._name

    @property
    def client(self) -> ClientT:
        """The client this plugin is included in."""
        if self._client is None:
            raise RuntimeError(
                f"Plugin '{self.name}' was not included in a client, '{type(self).__name__}.client' cannot be accessed until it is included in a client."
            )
        return self._client

    @property
    def default_enabled_guilds(self) -> t.Sequence[hikari.Snowflake] | hikari.UndefinedType:
        """The default guilds to enable commands in."""
        return self._default_enabled_guilds

    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        try:
            if self.error_handler is not None:
                await self.error_handler(ctx, exc)
            else:
                raise exc
        except Exception as exc:
            await self.client._on_error(ctx, exc)

    def _resolve_settings(self) -> _CommandSettings:
        settings = self._client._cmd_settings if self._client is not None else _CommandSettings.default()
        return settings.apply(self._cmd_settings)

    def _resolve_hooks(self) -> list[HookT[ClientT]]:
        return self.client._hooks + self._hooks

    def _resolve_post_hooks(self) -> list[PostHookT[ClientT]]:
        return self.client._post_hooks + self._post_hooks

    def _resolve_concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        return self._concurrency_limiter or self.client._concurrency_limiter

    def _client_include_hook(self, client: ClientT) -> None:
        if client._plugins.get(self.name) is not None:
            raise RuntimeError(f"Plugin '{self.name}' is already included in client.")

        self._client = client
        self._client._plugins[self.name] = self

        for command in itertools.chain(
            self._slash_commands.values(), self._user_commands.values(), self._message_commands.values()
        ):
            command._client_include_hook(client)

    def _client_remove_hook(self) -> None:
        if self._client is None:
            raise RuntimeError(f"Plugin '{self.name}' is not included in a client.")

        for command in itertools.chain(
            self._slash_commands.values(), self._user_commands.values(), self._message_commands.values()
        ):
            self.client._remove_command(command)

        self._client._plugins.pop(self.name)
        self._client = None

    def _add_command(self, command: CommandBase[ClientT, t.Any]) -> None:
        if isinstance(command, (SlashCommand, SlashGroup)):
            self._slash_commands[command.name] = command
        elif isinstance(command, UserCommand):
            self._user_commands[command.name] = command
        elif isinstance(command, MessageCommand):
            self._message_commands[command.name] = command
        else:
            raise TypeError(f"Unknown command type '{type(command).__name__}'.")

    @t.overload
    def include(self) -> t.Callable[[CallableCommandBase[ClientT, BuilderT]], CallableCommandBase[ClientT, BuilderT]]:
        ...

    @t.overload
    def include(self, command: CallableCommandBase[ClientT, BuilderT]) -> CallableCommandBase[ClientT, BuilderT]:
        ...

    def include(
        self, command: CallableCommandBase[ClientT, BuilderT] | None = None
    ) -> (
        CallableCommandBase[ClientT, BuilderT]
        | t.Callable[[CallableCommandBase[ClientT, BuilderT]], CallableCommandBase[ClientT, BuilderT]]
    ):
        """Add a command to this plugin.

        !!! note
            This should be the **last** (topmost) decorator on a command.

        Parameters
        ----------
        command : arc.CommandBase[ClientT, BuilderT]
            The command to include in this plugin.

        Raises
        ------
        RuntimeError
            If the command is already included in this plugin.
        """

        def decorator(command: CallableCommandBase[ClientT, BuilderT]) -> CallableCommandBase[ClientT, BuilderT]:
            if command.plugin is not None:
                raise ValueError(f"Command '{command.name}' is already registered with plugin '{command.plugin.name}'.")

            command._plugin_include_hook(self)
            return command

        if command is not None:
            return decorator(command)

        return decorator

    def include_slash_group(
        self,
        name: str,
        description: str = "No description provided.",
        *,
        guilds: t.Sequence[hikari.Snowflakeish | hikari.PartialGuild] | hikari.UndefinedType = hikari.UNDEFINED,
        autodefer: bool | AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED,
        is_dm_enabled: bool | hikari.UndefinedType = hikari.UNDEFINED,
        is_nsfw: bool | hikari.UndefinedType = hikari.UNDEFINED,
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        name_localizations: t.Mapping[hikari.Locale, str] | None = None,
        description_localizations: t.Mapping[hikari.Locale, str] | None = None,
    ) -> SlashGroup[ClientT]:
        """Add a new slash command group to this client.

        Parameters
        ----------
        name : str
            The name of the slash command group.
        description : str
            The description of the slash command group.
        guilds : t.Sequence[hikari.Snowflake] | hikari.UndefinedType
            The guilds to register the slash command group in
        autodefer : bool | AutodeferMode
            If True, all commands in this group will automatically defer if it is taking longer than 2 seconds to respond.
            This can be overridden on a per-subcommand basis.
        is_dm_enabled : bool
            Whether the slash command group is enabled in DMs
        default_permissions : hikari.Permissions | hikari.UndefinedType
            The default permissions for the slash command group
        name_localizations : dict[hikari.Locale, str]
            The name of the slash command group in different locales
        description_localizations : dict[hikari.Locale, str]
            The description of the slash command group in different locales
        is_nsfw : bool
            Whether the slash command group is only usable in NSFW channels

        Returns
        -------
        SlashGroup[te.Self]
            The slash command group that was created.

        !!! note
            Parameters left as `hikari.UNDEFINED` will be inherited from the parent plugin or client.

        Examples
        --------
        ```py
        group = client.include_slash_group("Group", "A group of commands.")

        @group.include
        @arc.slash_subcommand(name="Command", description="A command.")
        async def cmd(ctx: arc.GatewayContext) -> None:
            await ctx.respond("Hello!")
        ```
        """
        guild_ids = tuple(hikari.Snowflake(i) for i in guilds) if guilds is not hikari.UNDEFINED else hikari.UNDEFINED

        group: SlashGroup[ClientT] = SlashGroup(
            name=name,
            description=description,
            guilds=guild_ids,
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            is_dm_enabled=is_dm_enabled,
            default_permissions=default_permissions,
            name_localizations=name_localizations or {},
            description_localizations=description_localizations or {},
            is_nsfw=is_nsfw,
        )
        group._plugin_include_hook(self)
        return group

    @t.overload
    def inject_dependencies(self, func: t.Callable[P, T]) -> t.Callable[P, T]:
        ...

    @t.overload
    def inject_dependencies(self) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
        ...

    def inject_dependencies(
        self, func: t.Callable[P, T] | None = None
    ) -> t.Callable[P, T] | t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
        """First order decorator to inject dependencies into the decorated function.

        !!! warning
            This makes functions uncallable if the plugin is not added to a client.

        !!! note
            Command callbacks are automatically injected with dependencies,
            thus this decorator is not needed for them.

        Examples
        --------
        ```py
        class MyDependency:
            def __init__(self, value: str):
                self.value = value

        client = arc.GatewayClient(...)
        client.set_type_dependency(MyDependency, MyDependency("Hello!"))
        client.load_extension("foo")

        # In 'foo':

        plugin = arc.GatewayPlugin("My Plugin")

        @plugin.inject_dependencies
        def my_func(dep: MyDependency = arc.inject()) -> None:
            print(dep.value) # Prints "Hello!"

        @arc.loader
        def load(client: arc.GatewayClient) -> None:
            client.add_plugin(plugin)
        ```

        See Also
        --------
        - [`Client.set_type_dependency`][arc.client.Client.set_type_dependency]
            A method to set dependencies for the client.
        """

        def decorator(func: t.Callable[P, T]) -> t.Callable[P, T]:
            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def decorator_async(*args: P.args, **kwargs: P.kwargs) -> T:
                    if self._client is None:
                        raise RuntimeError(
                            f"Cannot inject dependencies into '{func.__name__}' before plugin '{self.name}' is included in a client."
                        )
                    return await self._client.injector.call_with_async_di(func, *args, **kwargs)

                return decorator_async  # pyright: ignore reportGeneralTypeIssues
            else:

                @functools.wraps(func)
                def decorator(*args: P.args, **kwargs: P.kwargs) -> T:
                    if self._client is None:
                        raise RuntimeError(
                            f"Cannot inject dependencies into '{func.__name__}' before plugin '{self.name}' is included in a client."
                        )
                    return self._client.injector.call_with_di(func, *args, **kwargs)

                return decorator

        if func is not None:
            return decorator(func)

        return decorator

    @t.overload
    def walk_commands(
        self, command_type: t.Literal[hikari.CommandType.USER], *, callable_only: bool = False
    ) -> t.Iterator[UserCommand[ClientT]]:
        ...

    @t.overload
    def walk_commands(
        self, command_type: t.Literal[hikari.CommandType.MESSAGE], *, callable_only: bool = False
    ) -> t.Iterator[MessageCommand[ClientT]]:
        ...

    @t.overload
    def walk_commands(
        self, command_type: t.Literal[hikari.CommandType.SLASH], *, callable_only: t.Literal[False]
    ) -> t.Iterator[SlashCommand[ClientT] | SlashSubCommand[ClientT] | SlashGroup[ClientT] | SlashSubGroup[ClientT]]:
        ...

    @t.overload
    def walk_commands(
        self, command_type: t.Literal[hikari.CommandType.SLASH], *, callable_only: t.Literal[True]
    ) -> t.Iterator[SlashCommand[ClientT] | SlashSubCommand[ClientT]]:
        ...

    def walk_commands(  # noqa: C901
        self, command_type: hikari.CommandType, *, callable_only: bool = False
    ) -> t.Iterator[t.Any]:
        """Iterate over all commands of a certain type added to this plugin.

        Parameters
        ----------
        command_type : hikari.CommandType
            The type of commands to return.
        callable_only : bool
            Whether to only return commands that are directly callable.
            If True, command groups and subgroups will be skipped.

        Yields
        ------
        CommandT[ClientT]
            The next command that matches the given criteria.

        Examples
        --------
        ```py
        for cmd in plugin.walk_commands(hikari.CommandType.SLASH):
            print(cmd.name)
        ```

        !!! tip
            To iterate over all types of commands, you may use [`itertools.chain()`][itertools.chain]:

            ```py
            import itertools

            for cmd in itertools.chain(
                plugin.walk_commands(hikari.CommandType.SLASH),
                plugin.walk_commands(hikari.CommandType.MESSAGE),
                plugin.walk_commands(hikari.CommandType.USER),
            ):
                print(cmd.name)
            ```
        """
        if hikari.CommandType.SLASH is command_type:
            for command in self._slash_commands.values():
                if isinstance(command, SlashCommand):
                    yield command
                    continue

                if not callable_only:
                    yield command

                for sub in command.children.values():
                    if isinstance(sub, SlashSubCommand):
                        yield sub
                        continue

                    if not callable_only:
                        yield sub

                    for subsub in sub.children.values():
                        yield subsub

        elif hikari.CommandType.MESSAGE is command_type:
            for command in self._message_commands.values():
                yield command

        elif hikari.CommandType.USER is command_type:
            for command in self._user_commands.values():
                yield command


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
