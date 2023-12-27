from __future__ import annotations

import abc
import functools
import importlib
import inspect
import logging
import pathlib
import sys
import traceback
import typing as t
from contextlib import suppress

import alluka
import hikari

from .command import MessageCommand, SlashCommand, SlashGroup, SlashSubCommand, SlashSubGroup, UserCommand
from .context import AutodeferMode, Context
from .errors import ExtensionLoadError, ExtensionUnloadError
from .events import CommandErrorEvent
from .internal.sync import _sync_commands
from .internal.types import AppT, BuilderT, EventCallbackT, EventT, ResponseBuilderT
from .plugin import Plugin

if t.TYPE_CHECKING:
    import typing_extensions as te

    from .command import CommandBase, SlashCommandLike

__all__ = ("Client", "GatewayClient", "RESTClient")


T = t.TypeVar("T")
P = t.ParamSpec("P")

logger = logging.getLogger(__name__)


class Client(t.Generic[AppT], abc.ABC):
    """A base class for an `arc` client.
    See [`GatewayClient`][arc.client.GatewayClient] and [`RESTClient`][arc.client.RESTClient] for implementations.

    Parameters
    ----------
    app : AppT
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | None, optional
        The guilds that slash commands will be registered in by default, by default None
    autosync : bool, optional
        Whether to automatically sync commands on startup, by default True
    """

    __slots__: t.Sequence[str] = (
        "_app",
        "_default_enabled_guilds",
        "_application",
        "_slash_commands",
        "_message_commands",
        "_user_commands",
        "_injector",
        "_autosync",
        "_plugins",
        "_loaded_extensions",
    )

    def __init__(
        self, app: AppT, *, default_enabled_guilds: t.Sequence[hikari.Snowflake] | None = None, autosync: bool = True
    ) -> None:
        self._app = app
        self._default_enabled_guilds = default_enabled_guilds
        self._application: hikari.Application | None = None
        self._slash_commands: dict[str, SlashCommandLike[te.Self]] = {}
        self._message_commands: dict[str, MessageCommand[te.Self]] = {}
        self._user_commands: dict[str, UserCommand[te.Self]] = {}
        self._injector: alluka.Client = alluka.Client()
        self._plugins: dict[str, Plugin[te.Self]] = {}
        self._loaded_extensions: list[str] = []
        self._autosync = autosync

    @property
    @abc.abstractmethod
    def is_rest(self) -> bool:
        """Whether the app is a rest client or a gateway client.

        This controls the client response flow, if True, `Client.handle_command_interaction` and `Client.handle_autocomplete_interaction`
        will return interaction response builders to be sent back to Discord, otherwise they will return None.
        """

    @property
    def app(self) -> AppT:
        """The application this client is for."""
        return self._app

    @property
    def rest(self) -> hikari.api.RESTClient:
        """The REST client of the underyling app."""
        return self.app.rest

    @property
    def application(self) -> hikari.Application | None:
        """The application object for this client. This is fetched on startup."""
        return self._application

    @property
    def injector(self) -> alluka.Client:
        """The injector for this client."""
        return self._injector

    @property
    def default_enabled_guilds(self) -> t.Sequence[hikari.Snowflake] | None:
        """The guilds that slash commands will be registered in by default."""
        return self._default_enabled_guilds

    @property
    def commands(self) -> t.Mapping[hikari.CommandType, t.Mapping[str, CommandBase[te.Self, t.Any]]]:
        """All commands added to this client, categorized by command type."""
        return {
            hikari.CommandType.SLASH: self.slash_commands,
            hikari.CommandType.MESSAGE: self._message_commands,
            hikari.CommandType.USER: self._user_commands,
        }

    @property
    def slash_commands(self) -> t.Mapping[str, SlashCommandLike[te.Self]]:
        """The slash commands added to this client. This only includes top-level commands and groups."""
        return self._slash_commands

    @property
    def message_commands(self) -> t.Mapping[str, MessageCommand[te.Self]]:
        """The message commands added to this client."""
        return self._message_commands

    @property
    def user_commands(self) -> t.Mapping[str, UserCommand[te.Self]]:
        """The user commands added to this client."""
        return self._user_commands

    @property
    def plugins(self) -> t.Mapping[str, Plugin[te.Self]]:
        """The plugins added to this client."""
        return self._plugins

    def _add_command(self, command: CommandBase[te.Self, t.Any]) -> None:
        """Add a command to this client. Called by include hooks."""
        if isinstance(command, (SlashCommand, SlashGroup)):
            self._add_slash_command(command)
        elif isinstance(command, MessageCommand):
            self._add_message_command(command)
        elif isinstance(command, UserCommand):
            self._add_user_command(command)

    def _remove_command(self, command: CommandBase[te.Self, t.Any]) -> None:
        """Remove a command from this client. Called by remove hooks."""
        if isinstance(command, (SlashCommand, SlashGroup)):
            self._slash_commands.pop(command.name, None)
        elif isinstance(command, MessageCommand):
            self._message_commands.pop(command.name, None)
        elif isinstance(command, UserCommand):
            self._user_commands.pop(command.name, None)

    def _add_slash_command(self, command: SlashCommandLike[te.Self]) -> None:
        """Add a slash command to this client."""
        if self.slash_commands.get(command.name) is not None:
            logger.warning(
                f"Shadowing already registered slash command '{command.name}'. Did you define multiple commands/groups with the same name?"
            )

        self._slash_commands[command.name] = command

    def _add_message_command(self, command: MessageCommand[te.Self]) -> None:
        """Add a message command to this client."""
        if self._message_commands.get(command.name) is not None:
            logger.warning(
                f"Shadowing already registered message command '{command.name}'. Did you define multiple commands with the same name?"
            )

        self._message_commands[command.name] = command

    def _add_user_command(self, command: UserCommand[te.Self]) -> None:
        """Add a user command to this client."""
        if self._user_commands.get(command.name) is not None:
            logger.warning(
                f"Shadowing already registered user command '{command.name}'. Did you define multiple commands with the same name?"
            )

        self._user_commands[command.name] = command

    async def _on_startup(self) -> None:
        """Called when the client is starting up.
        Fetches application, syncs commands, calls user-defined startup.
        """
        self._application = await self.app.rest.fetch_application()
        logger.debug(f"Fetched application: '{self.application}'")
        if self._autosync:
            await _sync_commands(self)
        await self.on_startup()

    async def on_startup(self) -> None:
        """Called when the client is starting up.
        Override for custom startup logic.
        """

    async def _on_shutdown(self) -> None:
        """Called when the client is shutting down.
        Reserved for internal shutdown logic.
        """
        await self.on_shutdown()

    async def on_shutdown(self) -> None:
        """Called when the client is shutting down.
        Override for custom shutdown logic.
        """

    async def _on_error(self, ctx: Context[te.Self], exception: Exception) -> None:
        await self.on_error(ctx, exception)

    async def on_error(self, context: Context[te.Self], exception: Exception) -> None:
        """Called when an error occurs in a command callback and all other error handlers have failed.

        Parameters
        ----------
        context : Context[te.Self]
            The context of the command.
        exception : Exception
            The exception that was raised.
        """
        print(f"Unhandled error in command '{context.command.name}' callback: {exception}", file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        with suppress(Exception):
            await context.respond("❌ Something went wrong. Please contact the bot developer.")

    async def on_command_interaction(self, interaction: hikari.CommandInteraction) -> ResponseBuilderT | None:
        """Should be called when a command interaction is sent by Discord.

        Parameters
        ----------
        interaction : hikari.CommandInteraction
            The interaction that was created.

        Returns
        -------
        ResponseBuilderT | None
            The response builder to send back to Discord, if using a REST client.
        """
        command = None

        if interaction.command_type is hikari.CommandType.SLASH:
            command = self.slash_commands.get(interaction.command_name)
        elif interaction.command_type is hikari.CommandType.MESSAGE:
            command = self.message_commands.get(interaction.command_name)
        elif interaction.command_type is hikari.CommandType.USER:
            command = self.user_commands.get(interaction.command_name)

        if command is None:
            logger.warning(f"Received interaction for unknown command '{interaction.command_name}'.")
            return

        fut = await command.invoke(interaction)

        if fut is not None:
            return await fut

    async def on_autocomplete_interaction(
        self, interaction: hikari.AutocompleteInteraction
    ) -> hikari.api.InteractionAutocompleteBuilder | None:
        """Should be called when an autocomplete interaction is sent by Discord.

        Parameters
        ----------
        interaction : hikari.AutocompleteInteraction
            The interaction that was created.

        Returns
        -------
        hikari.api.InteractionAutocompleteBuilder | None
            The autocomplete builder to send back to Discord, if using a REST client.
        """
        command = self.slash_commands.get(interaction.command_name)

        if command is None:
            logger.warning(f"Received autocomplete interaction for unknown command '{interaction.command_name}'.")
            return

        return await command._on_autocomplete(interaction)

    def include(self, command: CommandBase[te.Self, BuilderT]) -> CommandBase[te.Self, BuilderT]:
        """First-order decorator to add a command to this client.

        Parameters
        ----------
        command : CommandBase[te.Self, BuilderT]
            The command to add.
        """
        if command.plugin is not None:
            raise ValueError(f"Command '{command.name}' is already registered with plugin '{command.plugin.name}'.")

        if command.name in self.commands[command.command_type]:
            raise ValueError(f"Command '{command.name}' is already registered with this client.")

        command._client_include_hook(self)
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
    ) -> SlashGroup[te.Self]:
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
        async def cmd(ctx: arc.Context[arc.GatewayClient]) -> None:
            await ctx.respond("Hello!")
        ```
        """
        children: dict[str, SlashSubCommand[te.Self] | SlashSubGroup[te.Self]] = {}

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
        group._client_include_hook(self)
        return group

    def add_plugin(self, plugin: Plugin[te.Self]) -> None:
        """Add a plugin to this client.

        Parameters
        ----------
        plugin : Plugin[te.Self]
            The plugin to add.
        """
        plugin._client_include_hook(self)

    def remove_plugin(self, plugin: str | Plugin[te.Self]) -> None:
        """Remove a plugin from this client.

        Parameters
        ----------
        plugin : str | Plugin[te.Self]
            The plugin or name of the plugin to remove.

        Raises
        ------
        ValueError
            If there is no plugin with the given name.
        """
        if isinstance(plugin, Plugin):
            if plugin not in self.plugins.values():
                raise ValueError(f"Plugin '{plugin.name}' is not registered with this client.")
            return plugin._client_remove_hook()

        pg = self.plugins.get(plugin)

        if pg is None:
            raise ValueError(f"Plugin '{plugin}' is not registered with this client.")

        pg._client_remove_hook()

    def load_extension(self, path: str) -> te.Self:
        """Load a python module with path `path` as an extension.
        This will import the module, and call it's loader function.

        Parameters
        ----------
        path : str
            The path to the module to load.

        Returns
        -------
        te.Self
            The client for chaining calls.

        Raises
        ------
        ValueError
            If the module does not have a loader.

        Usage
        -----
        ```py
        client = arc.GatewayClient(...)
        client.load_extension("extension")

        # In extension.py

        plugin = arc.GatewayPlugin[arc.GatewayClient]("test_plugin")

        @arc.loader
        def loader(client: arc.GatewayClient) -> None:
            client.add_plugin(plugin)
        ```

        See Also
        --------
        - [`@arc.loader`][arc.extension.loader]
        - [`Client.load_extensions_from`][arc.client.Client.load_extensions_from]
        - [`Client.unload_extension`][arc.client.Client.unload_extension]
        """
        parents = path.split(".")
        name = parents.pop()

        pkg = ".".join(parents)

        if pkg:
            name = "." + name

        module = importlib.import_module(path, package=pkg)

        loader = getattr(module, "__arc_extension_loader__", None)

        if loader is None:
            raise ValueError(f"Module '{path}' does not have a loader.")

        self._loaded_extensions.append(path)
        loader(self)
        logger.info(f"Loaded extension: '{path}'")

        return self

    def load_extensions_from(self, dir_path: str | pathlib.Path, recursive: bool = False) -> te.Self:
        """Load all python modules in a directory as extensions.
        This will import the modules, and call their loader functions.

        Parameters
        ----------
        dir_path : str
            The path to the directory to load extensions from.
        recursive : bool, optional
            Whether to load extensions from subdirectories, by default False

        Returns
        -------
        te.Self
            The client for chaining calls.

        Raises
        ------
        ExtensionLoadError
            If `dir_path` does not exist or is not a directory.
        ExtensionLoadError
            If a module does not have a loader defined.
        """
        if isinstance(dir_path, str):
            dir_path = pathlib.Path(dir_path)

        try:
            dir_path.resolve().relative_to(pathlib.Path.cwd())
        except ValueError:
            raise ExtensionLoadError("dir_path must be relative to the current working directory.")

        if not dir_path.is_dir():
            raise ExtensionLoadError("dir_path must exist and be a directory.")

        globfunc = dir_path.rglob if recursive else dir_path.glob
        loaded = 0

        for file in globfunc(r"**/[!_]*.py"):
            module_path = ".".join(file.as_posix()[:-3].split("/"))
            self.load_extension(module_path)
            loaded += 1

        if loaded == 0:
            logger.warning(f"No extensions were found at '{dir_path}'.")

        return self

    def unload_extension(self, path: str) -> te.Self:
        """Unload a python module with path `path` as an extension.

        Parameters
        ----------
        path : str
            The path to the module to unload.

        Returns
        -------
        te.Self
            The client for chaining calls.

        Raises
        ------
        ExtensionUnloadError
            If the module does not have an unloader or is not loaded.
        """
        parents = path.split(".")
        name = parents.pop()

        pkg = ".".join(parents)

        if pkg:
            name = "." + name

        if path not in self._loaded_extensions:
            raise ExtensionUnloadError(f"Extension '{path}' is not loaded.")

        module = importlib.import_module(path, package=pkg)

        unloader = getattr(module, "__arc_extension_unloader__", None)

        if unloader is None:
            raise ExtensionUnloadError(f"Module '{path}' does not have an unloader.")

        unloader(self)
        self._loaded_extensions.remove(path)

        if module.__name__ in sys.modules:
            del sys.modules[module.__name__]

        return self

    def set_type_dependency(self, type_: t.Type[T], instance: T) -> None:
        """Set a type dependency for this client. This can then be injected into all arc callbacks.

        Parameters
        ----------
        type_ : t.Type[T]
            The type of the dependency.
        instance : T
            The instance of the dependency.

        Usage
        -----

        ```py
        class MyDependency:
            def __init__(self, value: str):
                self.value = value

        client.set_type_dependency(MyDependency, MyDependency("Hello!"))

        @client.include
        @arc.slash_command("cmd", "A command.")
        async def cmd(ctx: arc.Context[arc.GatewayClient], dep: arc.Injected[MyDependency]) -> None:
            await ctx.respond(dep.value)
        ```

        See Also
        --------
        - [`Client.get_type_dependency`][arc.client.Client.get_type_dependency]
            A method to get dependencies for the client.

        - [`Client.inject_dependencies`][arc.client.Client.inject_dependencies]
            A decorator to inject dependencies into arbitrary functions.
        """
        self._injector.set_type_dependency(type_, instance)

    def get_type_dependency(self, type_: t.Type[T]) -> hikari.UndefinedOr[T]:
        """Get a type dependency for this client.

        Parameters
        ----------
        type_ : t.Type[T]
            The type of the dependency.

        Returns
        -------
        hikari.UndefinedOr[T]
            The instance of the dependency, if it exists.
        """
        return self._injector.get_type_dependency(type_, default=hikari.UNDEFINED)

    def inject_dependencies(self, func: t.Callable[P, T]) -> t.Callable[P, T]:
        """First order decorator to inject dependencies into the decorated function.

        !!! note
            Command callbacks are automatically injected with dependencies,
            thus this decorator is not needed for them.

        Usage
        -----
        ```py
        class MyDependency:
            def __init__(self, value: str):
                self.value = value

        client.set_type_dependency(MyDependency, MyDependency("Hello!"))

        @client.inject_dependencies
        def my_func(dep: MyDependency = arc.inject()) -> None:
            print(dep.value)

        my_func() # Prints "Hello!"
        ```

        See Also
        --------
        - [`Client.set_type_dependency`][arc.client.Client.set_type_dependency]
            A method to set dependencies for the client.
        """
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def decorator_async(*args: P.args, **kwargs: P.kwargs) -> T:
                return await self.injector.call_with_async_di(func, *args, **kwargs)

            return decorator_async  # pyright: ignore reportGeneralTypeIssues
        else:

            @functools.wraps(func)
            def decorator(*args: P.args, **kwargs: P.kwargs) -> T:
                return self.injector.call_with_di(func, *args, **kwargs)

            return decorator

    async def resync_commands(self) -> None:
        """Synchronize the commands registered in this client with Discord.

        !!! warning
            Calling this is expensive, and should only be done when absolutely necessary.
            The client automatically syncs commands on startup, unless the `autosync` parameter
            is set to `False` when creating the client.

        Raises
        ------
        RuntimeError
            If `Client.application` is `None`.
            This usually only happens if `Client.resync_commands` is called before `Client.on_startup`.
        """
        await _sync_commands(self)

    async def purge_all_commands(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild] | None = None) -> None:
        """Purge all commands registered on Discord. This can be used to clean up commands.

        Parameters
        ----------
        guild : hikari.SnowflakeishOr[hikari.PartialGuild] | None, optional
            The guild to purge commands from, by default None
            If a `guild` is not provided, this will purge global commands.

        !!! warning
            This will remove all commands registered on Discord, **including commands not registered by this client**.

        Raises
        ------
        RuntimeError
            If `Client.application` is `None`.
            This usually only happens if `Client.purge_all_commands` is called before `Client.on_startup`.
        """
        if self.application is None:
            raise RuntimeError(f"Cannot purge commands before '{type(self).__name__}.application' is fetched.")

        if guild is not None:
            guild_id = hikari.Snowflake(guild)
            await self.rest.set_application_commands(self.application, [], guild_id)
        else:
            await self.rest.set_application_commands(self.application, [])


class GatewayClient(Client[hikari.GatewayBotAware]):
    """A base class for an arc client with `hikari.GatewayBotAware` support.
    If you want to use a `hikari.RESTBotAware`, use `RESTClient` instead.

    Parameters
    ----------
    app : hikari.GatewayBot
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | None, optional
        The guilds that slash commands will be registered in by default, by default None
    autosync : bool, optional
        Whether to automatically sync commands on startup, by default True

    Usage
    -----
    ```py
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)

    ...
    ```
    """

    __slots__: t.Sequence[str] = ()

    def __init__(
        self,
        app: hikari.GatewayBotAware,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflake] | None = None,
        autosync: bool = True,
    ) -> None:
        super().__init__(app, default_enabled_guilds=default_enabled_guilds, autosync=autosync)
        self.app.event_manager.subscribe(hikari.StartedEvent, self._on_gatewaybot_startup)
        self.app.event_manager.subscribe(hikari.StoppingEvent, self._on_gatewaybot_shutdown)
        self.app.event_manager.subscribe(hikari.InteractionCreateEvent, self._on_gatewaybot_interaction_create)

    @property
    def is_rest(self) -> bool:
        """Whether this client is a REST client."""
        return False

    @property
    def cache(self) -> hikari.api.Cache:
        """The cache for this client."""
        return self.app.cache

    async def _on_gatewaybot_startup(self, event: hikari.StartedEvent) -> None:
        await self._on_startup()

    async def _on_gatewaybot_shutdown(self, event: hikari.StoppingEvent) -> None:
        await self._on_shutdown()

    async def _on_gatewaybot_interaction_create(self, event: hikari.InteractionCreateEvent) -> None:
        if isinstance(event.interaction, hikari.CommandInteraction):
            await self.on_command_interaction(event.interaction)
        elif isinstance(event.interaction, hikari.AutocompleteInteraction):
            await self.on_autocomplete_interaction(event.interaction)

    async def _on_error(self, ctx: Context[te.Self], exception: Exception) -> None:
        if not self.app.event_manager.get_listeners(CommandErrorEvent):
            return await super()._on_error(ctx, exception)

        self.app.event_manager.dispatch(CommandErrorEvent(self, ctx, exception))

    def listen(self, *event_types: t.Type[EventT]) -> t.Callable[[EventCallbackT[EventT]], EventCallbackT[EventT]]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        *event_types : t.Type[EventT] | None
            The event types to subscribe to. The implementation may allow this
            to be undefined. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

            `EventT` must be a subclass of `hikari.events.base_events.Event`.

        Returns
        -------
        t.Callable[[EventT], EventT]
            A decorator for a coroutine function that passes it to
            `EventManager.subscribe` before returning the function
            reference.
        """
        return self.app.event_manager.listen(*event_types)


class RESTClient(Client[hikari.RESTBotAware]):
    """A base class for an arc client with `hikari.RESTBotAware` support.
    If you want to use `hikari.GatewayBotAware`, use `GatewayClient` instead.

    Parameters
    ----------
    app : hikari.RESTBot
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | None, optional
        The guilds that slash commands will be registered in by default, by default None
    autosync : bool, optional
        Whether to automatically sync commands on startup, by default True


    Usage
    -----
    ```py
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)

    ...
    ```

    !!! warning
        The client will take over the `hikari.CommandInteraction` and `hikari.AutocompleteInteraction` listeners of the passed bot.
    """

    __slots__: t.Sequence[str] = ()

    def __init__(
        self,
        app: hikari.RESTBotAware,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflake] | None = None,
        autosync: bool = True,
    ) -> None:
        super().__init__(app, default_enabled_guilds=default_enabled_guilds, autosync=autosync)
        self.app.add_startup_callback(self._on_restbot_startup)
        self.app.add_shutdown_callback(self._on_restbot_shutdown)
        self.app.interaction_server.set_listener(
            hikari.CommandInteraction, self._on_restbot_interaction_create, replace=True
        )
        self.app.interaction_server.set_listener(
            hikari.AutocompleteInteraction, self._on_restbot_autocomplete_interaction_create, replace=True
        )

    @property
    def is_rest(self) -> bool:
        """Whether this client is a REST client."""
        return True

    async def _on_restbot_startup(self, bot: hikari.RESTBotAware) -> None:
        await self._on_startup()
        await self.on_restbot_startup(bot)

    async def on_restbot_startup(self, bot: hikari.RESTBotAware) -> None:
        """A function that is called when the client is started.

        Parameters
        ----------
        bot : hikari.RESTBotAware
            The bot that was started.
        """

    async def _on_restbot_shutdown(self, bot: hikari.RESTBotAware) -> None:
        await self._on_shutdown()
        await self.on_restbot_shutdown(bot)

    async def on_restbot_shutdown(self, bot: hikari.RESTBotAware) -> None:
        """A function that is called when the client is shut down.

        Parameters
        ----------
        bot : hikari.RESTBotAware
            The bot that was shut down.
        """

    async def _on_restbot_interaction_create(self, interaction: hikari.CommandInteraction) -> ResponseBuilderT:
        builder = await self.on_command_interaction(interaction)
        assert builder is not None
        return builder

    async def _on_restbot_autocomplete_interaction_create(
        self, interaction: hikari.AutocompleteInteraction
    ) -> hikari.api.InteractionAutocompleteBuilder:
        builder = await self.on_autocomplete_interaction(interaction)
        assert builder is not None
        return builder


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
