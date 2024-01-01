from __future__ import annotations

import abc
import functools
import inspect
import itertools
import typing as t

import hikari

from arc.abc.error_handler import HasErrorHandler
from arc.abc.hookable import Hookable
from arc.command import MessageCommand, SlashCommand, SlashGroup, UserCommand
from arc.context import AutodeferMode, Context
from arc.internal.types import BuilderT, ClientT, ErrorHandlerCallbackT, HookT, PostHookT, SlashCommandLike

if t.TYPE_CHECKING:
    from arc.abc.command import CommandBase
    from arc.command import SlashSubCommand, SlashSubGroup

__all__ = ("PluginBase",)

P = t.ParamSpec("P")
T = t.TypeVar("T")


class PluginBase(HasErrorHandler[ClientT], Hookable[ClientT]):
    """An abstract base class for plugins.

    Parameters
    ----------
    name : str
        The name of this plugin. This must be unique across all plugins.
    """

    def __init__(
        self, name: str, *, default_enabled_guilds: hikari.UndefinedOr[t.Sequence[hikari.Snowflake]] = hikari.UNDEFINED
    ) -> None:
        self._client: ClientT | None = None
        self._name = name
        self._slash_commands: dict[str, SlashCommandLike[ClientT]] = {}
        self._user_commands: dict[str, UserCommand[ClientT]] = {}
        self._message_commands: dict[str, MessageCommand[ClientT]] = {}
        self._default_enabled_guilds = default_enabled_guilds
        self._error_handler: ErrorHandlerCallbackT[ClientT] | None = None
        self._hooks: list[HookT[ClientT]] = []
        self._post_hooks: list[PostHookT[ClientT]] = []

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this plugin."""
        return self._error_handler

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
    def default_enabled_guilds(self) -> hikari.UndefinedOr[t.Sequence[hikari.Snowflake]]:
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

    def _resolve_hooks(self) -> list[HookT[ClientT]]:
        return self._hooks

    def _resolve_post_hooks(self) -> list[PostHookT[ClientT]]:
        return self._post_hooks

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

    def include(self, command: CommandBase[ClientT, BuilderT]) -> CommandBase[ClientT, BuilderT]:
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
        if command.plugin is not None:
            raise ValueError(f"Command '{command.name}' is already registered with plugin '{command.plugin.name}'.")

        command._plugin_include_hook(self)
        return command

    def include_slash_group(
        self,
        name: str,
        description: str = "No description provided.",
        *,
        guilds: hikari.UndefinedOr[t.Sequence[hikari.Snowflake]] = hikari.UNDEFINED,
        autodefer: bool | AutodeferMode = True,
        is_dm_enabled: bool = True,
        default_permissions: hikari.UndefinedOr[hikari.Permissions] = hikari.UNDEFINED,
        name_localizations: dict[hikari.Locale, str] | None = None,
        description_localizations: dict[hikari.Locale, str] | None = None,
        is_nsfw: bool = False,
    ) -> SlashGroup[ClientT]:
        """Add a new slash command group to this client.

        Parameters
        ----------
        name : str
            The name of the slash command group.
        description : str
            The description of the slash command group.
        guilds : hikari.UndefinedOr[t.Sequence[hikari.Snowflake]], optional
            The guilds to register the slash command group in, by default hikari.UNDEFINED
        autodefer : bool | AutodeferMode, optional
            If True, all commands in this group will automatically defer if it is taking longer than 2 seconds to respond.
            This can be overridden on a per-subcommand basis.
        is_dm_enabled : bool, optional
            Whether the slash command group is enabled in DMs, by default True
        default_permissions : hikari.UndefinedOr[hikari.Permissions], optional
            The default permissions for the slash command group, by default hikari.UNDEFINED
        name_localizations : dict[hikari.Locale, str], optional
            The name of the slash command group in different locales, by default None
        description_localizations : dict[hikari.Locale, str], optional
            The description of the slash command group in different locales, by default None
        is_nsfw : bool, optional
            Whether the slash command group is only usable in NSFW channels, by default False

        Returns
        -------
        SlashGroup[te.Self]
            The slash command group that was created.

        Usage
        -----
        ```py
        group = client.include_slash_group("Group", "A group of commands.")

        @group.include
        @arc.slash_subcommand(name="Command", description="A command.")
        async def cmd(ctx: arc.GatewayContext) -> None:
            await ctx.respond("Hello!")
        ```
        """
        children: dict[str, SlashSubCommand[ClientT] | SlashSubGroup[ClientT]] = {}

        group = SlashGroup(
            name=name,
            description=description,
            children=children,
            guilds=guilds,
            autodefer=AutodeferMode(autodefer),
            is_dm_enabled=is_dm_enabled,
            default_permissions=default_permissions,
            name_localizations=name_localizations or {},
            description_localizations=description_localizations or {},
            is_nsfw=is_nsfw,
        )
        group._plugin_include_hook(self)
        return group

    def inject_dependencies(self, func: t.Callable[P, T]) -> t.Callable[P, T]:
        """First order decorator to inject dependencies into the decorated function.

        !!! warning
            This makes functions uncallable if the plugin is not added to a client.

        !!! note
            Command callbacks are automatically injected with dependencies,
            thus this decorator is not needed for them.

        Usage
        -----
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
