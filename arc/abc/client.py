from __future__ import annotations

import abc
import asyncio
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

from arc.abc.command import _CommandSettings
from arc.abc.plugin import PluginBase
from arc.command.message import MessageCommand
from arc.command.slash import SlashCommand, SlashGroup
from arc.command.user import UserCommand
from arc.context import AutodeferMode, Context
from arc.errors import ExtensionLoadError, ExtensionUnloadError
from arc.internal.sync import _sync_commands
from arc.internal.types import (
    AppT,
    BuilderT,
    CommandLocaleRequestT,
    CustomLocaleRequestT,
    ErrorHandlerCallbackT,
    HookT,
    LifeCycleHookT,
    OptionLocaleRequestT,
    PostHookT,
    ResponseBuilderT,
)
from arc.locale import CommandLocaleRequest, LocaleResponse, OptionLocaleRequest

if t.TYPE_CHECKING:
    import typing_extensions as te

    from arc.abc.command import CommandBase
    from arc.command import SlashCommandLike

__all__ = ("Client",)


T = t.TypeVar("T")
P = t.ParamSpec("P")

logger = logging.getLogger(__name__)


class Client(t.Generic[AppT], abc.ABC):
    """The abstract base class for an `arc` client.
    See [`GatewayClientBase`][arc.client.GatewayClientBase] and [`RESTClientBase`][arc.client.RESTClientBase] for implementations.

    Parameters
    ----------
    app : AppT
        The application this client is for.
    default_enabled_guilds : t.Sequence[hikari.Snowflake] | None
        The guilds that slash commands will be registered in by default
    autosync : bool
        Whether to automatically sync commands on startup
    autodefer : bool | AutodeferMode
        Whether to automatically defer commands that take longer than 2 seconds to respond
        This applies to all commands, and can be overridden on a per-command basis.
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for commands
        This applies to all commands, and can be overridden on a per-command basis.
    is_nsfw : bool
        Whether to mark commands as NSFW
        This applies to all commands, and can be overridden on a per-command basis.
    is_dm_enabled : bool
        Whether to enable commands in DMs
        This applies to all commands, and can be overridden on a per-command basis.
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
        "_hooks",
        "_post_hooks",
        "_owner_ids",
        "_error_handler",
        "_startup_hook",
        "_shutdown_hook",
        "_provided_locales",
        "_command_locale_provider",
        "_option_locale_provider",
        "_custom_locale_provider",
        "_cmd_settings",
    )

    def __init__(
        self,
        app: AppT,
        *,
        default_enabled_guilds: t.Sequence[hikari.Snowflakeish | hikari.PartialGuild]
        | hikari.UndefinedType = hikari.UNDEFINED,
        autosync: bool = True,
        autodefer: bool | AutodeferMode = True,
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        is_nsfw: bool = False,
        is_dm_enabled: bool = True,
        provided_locales: t.Sequence[hikari.Locale] | None = None,
    ) -> None:
        self._app = app
        self._default_enabled_guilds = (
            tuple(hikari.Snowflake(i) for i in default_enabled_guilds)
            if default_enabled_guilds is not hikari.UNDEFINED
            else hikari.UNDEFINED
        )
        self._autosync = autosync
        self._provided_locales: t.Sequence[hikari.Locale] | None = provided_locales
        self._cmd_settings = _CommandSettings(
            autodefer=AutodeferMode(autodefer),
            default_permissions=default_permissions,
            is_nsfw=is_nsfw,
            is_dm_enabled=is_dm_enabled,
        )

        self._application: hikari.Application | None = None
        self._slash_commands: dict[str, SlashCommandLike[te.Self]] = {}
        self._message_commands: dict[str, MessageCommand[te.Self]] = {}
        self._user_commands: dict[str, UserCommand[te.Self]] = {}
        self._injector: alluka.Client = alluka.Client()
        self._plugins: dict[str, PluginBase[te.Self]] = {}
        self._loaded_extensions: list[str] = []
        self._hooks: list[HookT[te.Self]] = []
        self._post_hooks: list[PostHookT[te.Self]] = []
        self._owner_ids: list[hikari.Snowflake] = []
        self._error_handler: ErrorHandlerCallbackT[te.Self] | None = None
        self._startup_hook: LifeCycleHookT[te.Self] | None = None
        self._shutdown_hook: LifeCycleHookT[te.Self] | None = None
        self._command_locale_provider: CommandLocaleRequestT | None = None
        self._option_locale_provider: OptionLocaleRequestT | None = None
        self._custom_locale_provider: CustomLocaleRequestT | None = None

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
    def default_enabled_guilds(self) -> t.Sequence[hikari.Snowflake] | hikari.UndefinedType:
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
    def plugins(self) -> t.Mapping[str, PluginBase[te.Self]]:
        """The plugins added to this client."""
        return self._plugins

    @property
    def hooks(self) -> t.MutableSequence[HookT[te.Self]]:
        """The pre-execution hooks for this client."""
        return self._hooks

    @property
    def post_hooks(self) -> t.MutableSequence[PostHookT[te.Self]]:
        """The post-execution hooks for this client."""
        return self._post_hooks

    @property
    def owner_ids(self) -> t.Sequence[hikari.Snowflake]:
        """The IDs of the owners of this application."""
        return self._owner_ids

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[te.Self] | None:
        """The error handler for this client."""
        return self._error_handler

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
        self._slash_commands[command.name] = command

    def _add_message_command(self, command: MessageCommand[te.Self]) -> None:
        """Add a message command to this client."""
        self._message_commands[command.name] = command

    def _add_user_command(self, command: UserCommand[te.Self]) -> None:
        """Add a user command to this client."""
        self._user_commands[command.name] = command

    async def _on_startup(self) -> None:
        """Called when the client is starting up.
        Fetches application, syncs commands, calls user-defined startup.
        """
        self._application = await self.app.rest.fetch_application()

        owner_ids = [self._application.owner.id]

        if self._application.team is not None:
            owner_ids.extend(member for member in self._application.team.members)

        self._owner_ids = owner_ids

        logger.debug(f"Fetched application: '{self.application}'")
        if self._autosync:
            await _sync_commands(self)

        if self._startup_hook:
            await self._startup_hook(self)

    async def _on_shutdown(self) -> None:
        """Called when the client is shutting down.
        Reserved for internal shutdown logic.
        """
        if self._shutdown_hook:
            await self._shutdown_hook(self)

    async def _on_error(self, ctx: Context[te.Self], exception: Exception) -> None:
        if self._error_handler is not None:
            try:
                return await self._error_handler(ctx, exception)
            except Exception as e:
                exception = e

        print(f"Unhandled error in command '{ctx.command.name}' callback: {exception}", file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        with suppress(Exception):
            # Try to respond to make autodefer less jarring when a command fails.
            if not ctx._issued_response and ctx.is_valid:
                await ctx.respond("❌ Something went wrong. Please contact the bot developer.")

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

        match interaction.command_type:
            case hikari.CommandType.SLASH:
                command = self.slash_commands.get(interaction.command_name)
            case hikari.CommandType.MESSAGE:
                command = self.message_commands.get(interaction.command_name)
            case hikari.CommandType.USER:
                command = self.user_commands.get(interaction.command_name)
            case _:
                pass

        if command is None:
            logger.warning(f"Received interaction for unknown command '{interaction.command_name}'.")
            return

        fut = await command.invoke(interaction)

        if fut is None:
            return

        try:
            return await asyncio.wait_for(fut, timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timed out waiting for response from command: '{interaction.command_name} ({interaction.command_type})'"
                f" Did you forget to respond?"
            )

    def _provide_command_locale(self, request: CommandLocaleRequest) -> LocaleResponse:
        """Provide a locale for a command."""
        if self._command_locale_provider is None:
            return LocaleResponse(name=request.command.name, description=getattr(request.command, "description", None))

        return self._command_locale_provider(request)

    def _provide_option_locale(self, request: OptionLocaleRequest) -> LocaleResponse:
        """Provide a locale for an option."""
        if self._option_locale_provider is None:
            return LocaleResponse(name=request.option.name, description=request.option.description)

        return self._option_locale_provider(request)

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

    @t.overload
    def include(self) -> t.Callable[[CommandBase[te.Self, BuilderT]], CommandBase[te.Self, BuilderT]]:
        ...

    @t.overload
    def include(self, command: CommandBase[te.Self, BuilderT]) -> CommandBase[te.Self, BuilderT]:
        ...

    def include(
        self, command: CommandBase[te.Self, BuilderT] | None = None
    ) -> CommandBase[te.Self, BuilderT] | t.Callable[[CommandBase[te.Self, BuilderT]], CommandBase[te.Self, BuilderT]]:
        """Decorator to add a command to this client.

        !!! note
            This should be the **last** (topmost) decorator on a command.

        Parameters
        ----------
        command : CommandBase[te.Self, BuilderT]
            The command to add.

        Raises
        ------
        RuntimeError
            If the command is already added to a plugin.

        Usage
        -----
        ```py
        @client.include # Add the command to the client.
        @arc.slash_command("cmd", "A command.")
        async def cmd(ctx: arc.GatewayContext) -> None:
            ...
        ```
        """

        def decorator(command: CommandBase[te.Self, BuilderT]) -> CommandBase[te.Self, BuilderT]:
            if command.plugin is not None:
                raise RuntimeError(
                    f"Command '{command.name}' is already registered with plugin '{command.plugin.name}'."
                    f"\nYou should use '{type(self).__name__}.add_plugin()' to add the entire plugin to the client."
                )

            if existing := self.commands[command.command_type].get(command.name):
                logger.warning(
                    f"Shadowing already registered command '{command.name}'. Did you define multiple commands with the same name?"
                )
                existing._client_remove_hook(self)

            command._client_include_hook(self)
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
        default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
        name_localizations: t.Mapping[hikari.Locale, str] | None = None,
        description_localizations: t.Mapping[hikari.Locale, str] | None = None,
        is_nsfw: bool = False,
    ) -> SlashGroup[te.Self]:
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
            Parameters left as `hikari.UNDEFINED` will be inherited from the parent client.

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
        guild_ids = tuple(hikari.Snowflake(i) for i in guilds) if guilds is not hikari.UNDEFINED else hikari.UNDEFINED

        group: SlashGroup[te.Self] = SlashGroup(
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
        group._client_include_hook(self)
        return group

    def add_plugin(self, plugin: PluginBase[te.Self]) -> te.Self:
        """Add a plugin to this client.

        Parameters
        ----------
        plugin : Plugin[te.Self]
            The plugin to add.

        Returns
        -------
        te.Self
            The client for chaining calls.
        """
        plugin._client_include_hook(self)
        return self

    def remove_plugin(self, plugin: str | PluginBase[te.Self]) -> te.Self:
        """Remove a plugin from this client.

        Parameters
        ----------
        plugin : str | Plugin[te.Self]
            The plugin or name of the plugin to remove.

        Raises
        ------
        ValueError
            If there is no plugin with the given name.

        Returns
        -------
        te.Self
            The client for chaining calls.
        """
        if isinstance(plugin, PluginBase):
            if plugin not in self.plugins.values():
                raise ValueError(f"Plugin '{plugin.name}' is not registered with this client.")
            plugin._client_remove_hook()
            return self

        pg = self.plugins.get(plugin)

        if pg is None:
            raise ValueError(f"Plugin '{plugin}' is not registered with this client.")

        pg._client_remove_hook()
        return self

    @t.overload
    def add_hook(self, hook: HookT[te.Self]) -> te.Self:
        ...

    @t.overload
    def add_hook(self) -> t.Callable[[HookT[te.Self]], HookT[te.Self]]:
        ...

    def add_hook(self, hook: HookT[te.Self] | None = None) -> te.Self | t.Callable[[HookT[te.Self]], HookT[te.Self]]:
        """Add a pre-execution hook to this client.
        This hook will be executed before **every command** that is added to this client.

        Parameters
        ----------
        hook : HookT[te.Self]
            The hook to add.

        Returns
        -------
        te.Self
            The client for chaining calls.

        See Also
        --------
        - [`Client.add_post_hook`][arc.client.Client.add_post_hook]
        """
        if hook is not None:
            self._hooks.append(hook)
            return self

        def decorator(hook: HookT[te.Self]) -> HookT[te.Self]:
            self._hooks.append(hook)
            return hook

        return decorator

    @t.overload
    def add_post_hook(self, hook: PostHookT[te.Self]) -> te.Self:
        ...

    @t.overload
    def add_post_hook(self) -> t.Callable[[PostHookT[te.Self]], PostHookT[te.Self]]:
        ...

    def add_post_hook(
        self, hook: PostHookT[te.Self] | None = None
    ) -> te.Self | t.Callable[[PostHookT[te.Self]], PostHookT[te.Self]]:
        """Add a post-execution hook to this client.
        This hook will be executed after **every command** that is added to this client.

        !!! warning
            Post-execution hooks will be called even if the command callback raises an exception.

        Parameters
        ----------
        hook : PostHookT[te.Self]
            The hook to add.

        Returns
        -------
        te.Self
            The client for chaining calls.

        See Also
        --------
        - [`Client.add_hook`][arc.client.Client.add_hook]
        """
        if hook is not None:
            self._post_hooks.append(hook)
            return self

        def decorator(hook: PostHookT[te.Self]) -> PostHookT[te.Self]:
            self._post_hooks.append(hook)
            return hook

        return decorator

    @t.overload
    def set_error_handler(self, handler: ErrorHandlerCallbackT[te.Self]) -> None:
        ...

    @t.overload
    def set_error_handler(self) -> t.Callable[[ErrorHandlerCallbackT[te.Self]], None]:
        ...

    def set_error_handler(
        self, handler: ErrorHandlerCallbackT[te.Self] | None = None
    ) -> None | t.Callable[[ErrorHandlerCallbackT[te.Self]], None]:
        """Decorator to set the error handler for this client.

        This will be called when a command callback raises an exception
        that is not handled by any other error handlers.

        Parameters
        ----------
        handler : ErrorHandlerCallbackT[te.Self]
            The error handler to set.

        Usage
        -----
        ```py
        @client.set_error_handler
        async def error_handler_func(ctx: arc.GatewayContext, exception: Exception) -> None:
            await ctx.respond(f"❌ Something went wrong: {exception}")
        ```

        Or, as a function:

        ```py
        client.set_error_handler(error_handler_func)
        ```
        """
        if handler is not None:
            self._error_handler = handler
            return

        def decorator(handler: ErrorHandlerCallbackT[te.Self]) -> None:
            self._error_handler = handler

        return decorator

    @t.overload
    def set_startup_hook(self, hook: LifeCycleHookT[te.Self]) -> None:
        ...

    @t.overload
    def set_startup_hook(self) -> t.Callable[[LifeCycleHookT[te.Self]], None]:
        ...

    def set_startup_hook(
        self, hook: LifeCycleHookT[te.Self] | None = None
    ) -> None | t.Callable[[LifeCycleHookT[te.Self]], None]:
        """Decorator to set the startup hook for this client.

        This will be called when the client starts up.

        Parameters
        ----------
        hook : LifeCycleHookT[te.Self]
            The startup hook to set.

        Usage
        -----
        ```py
        @client.set_startup_hook
        async def startup_hook(client: arc.GatewayClient) -> None:
            print("Client started up!")
        ```

        Or, as a function:

        ```py
        client.set_startup_hook(startup_hook)
        ```
        """
        if hook is not None:
            self._startup_hook = hook
            return

        def decorator(handler: LifeCycleHookT[te.Self]) -> None:
            self._startup_hook = handler

        return decorator

    @t.overload
    def set_shutdown_hook(self, hook: LifeCycleHookT[te.Self]) -> None:
        ...

    @t.overload
    def set_shutdown_hook(self) -> t.Callable[[LifeCycleHookT[te.Self]], None]:
        ...

    def set_shutdown_hook(
        self, hook: LifeCycleHookT[te.Self] | None = None
    ) -> None | t.Callable[[LifeCycleHookT[te.Self]], None]:
        """Decorator to set the shutdown hook for this client.

        This will be called when the client shuts down.

        Parameters
        ----------
        hook : LifeCycleHookT[te.Self]
            The shutdown hook to set.

        Usage
        -----
        ```py
        @client.set_shutdown_hook
        async def shutdown_hook(client: arc.GatewayClient) -> None:
            print("Client shut down!")
        ```

        Or, as a function:

        ```py
        client.set_shutdown_hook(shutdown_hook)
        ```
        """
        if hook is not None:
            self._shutdown_hook = hook
            return

        def decorator(handler: LifeCycleHookT[te.Self]) -> None:
            self._shutdown_hook = handler

        return decorator

    @t.overload
    def set_command_locale_provider(self, provider: CommandLocaleRequestT) -> None:
        ...

    @t.overload
    def set_command_locale_provider(self) -> t.Callable[[CommandLocaleRequestT], None]:
        ...

    def set_command_locale_provider(
        self, provider: CommandLocaleRequestT | None = None
    ) -> None | t.Callable[[CommandLocaleRequestT], None]:
        """Decorator to set the command locale provider for this client.

        This will be called for each command for each locale.

        Parameters
        ----------
        provider : CommandLocaleRequestT
            The command locale provider to set.

        Usage
        -----
        ```py
        @client.set_command_locale_provider
        def command_locale_provider(request: arc.CommandLocaleRequest) -> arc.LocaleResponse:
            ...
        ```

        Or, as a function:

        ```py
        client.set_command_locale_provider(command_locale_provider)
        ```
        """
        if provider is not None:
            self._command_locale_provider = provider
            return

        def decorator(provider: CommandLocaleRequestT) -> None:
            self._command_locale_provider = provider

        return decorator

    @t.overload
    def set_option_locale_provider(self, provider: OptionLocaleRequestT) -> None:
        ...

    @t.overload
    def set_option_locale_provider(self) -> t.Callable[[OptionLocaleRequestT], None]:
        ...

    def set_option_locale_provider(
        self, provider: OptionLocaleRequestT | None = None
    ) -> None | t.Callable[[OptionLocaleRequestT], None]:
        """Decorator to set the option locale provider for this client.

        This will be called for each option of each command for each locale.

        Parameters
        ----------
        provider : OptionLocaleRequestT
            The option locale provider to set.

        Usage
        -----
        ```py
        @client.set_option_locale_provider
        def option_locale_provider(request: arc.OptionLocaleRequest) -> arc.LocaleResponse:
            ...
        ```

        Or, as a function:

        ```py
        client.set_option_locale_provider(option_locale_provider)
        ```
        """
        if provider is not None:
            self._option_locale_provider = provider
            return

        def decorator(provider: OptionLocaleRequestT) -> None:
            self._option_locale_provider = provider

        return decorator

    @t.overload
    def set_custom_locale_provider(self, provider: CustomLocaleRequestT) -> None:
        ...

    @t.overload
    def set_custom_locale_provider(self) -> t.Callable[[CustomLocaleRequestT], None]:
        ...

    def set_custom_locale_provider(
        self, provider: CustomLocaleRequestT | None = None
    ) -> None | t.Callable[[CustomLocaleRequestT], None]:
        """Decorator to set the custom locale provider for this client.

        This will be called for each custom locale request performed via [`Context.loc()`][arc.context.base.Context.loc].

        Parameters
        ----------
        provider : CustomLocaleRequestT
            The custom locale provider to set.

        Usage
        -----
        ```py
        @client.set_custom_locale_provider
        def custom_locale_provider(request: arc.CustomLocaleRequest) -> str:
            ...
        ```

        Or, as a function:

        ```py
        client.set_custom_locale_provider(custom_locale_provider)
        ```
        """
        if provider is not None:
            self._custom_locale_provider = provider
            return

        def decorator(provider: CustomLocaleRequestT) -> None:
            self._custom_locale_provider = provider

        return decorator

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

        plugin = arc.GatewayPlugin("test_plugin")

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
        recursive : bool
            Whether to load extensions from subdirectories

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

        Usage
        -----
        ```py
        client = arc.GatewayClient(...)
        client.load_extensions_from("extensions/foo")
        ```

        See Also
        --------
        - [`@arc.loader`][arc.extension.loader]
        - [`Client.load_extension`][arc.client.Client.load_extension]
        - [`Client.unload_extension`][arc.client.Client.unload_extension]
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

        See Also
        --------
        - [`Client.load_extension`][arc.client.Client.load_extension]
        - [`Client.load_extensions_from`][arc.client.Client.load_extensions_from]
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

    def set_type_dependency(self, type_: t.Type[T], instance: T) -> te.Self:
        """Set a type dependency for this client. This can then be injected into all arc callbacks.

        Parameters
        ----------
        type_ : t.Type[T]
            The type of the dependency.
        instance : T
            The instance of the dependency.

        Returns
        -------
        te.Self
            The client for chaining calls.

        Usage
        -----

        ```py
        class MyDependency:
            def __init__(self, value: str):
                self.value = value

        client.set_type_dependency(MyDependency, MyDependency("Hello!"))

        @client.include
        @arc.slash_command("cmd", "A command.")
        async def cmd(ctx: arc.GatewayContext, dep: MyDependency = arc.inject()) -> None:
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
        return self

    def get_type_dependency(self, type_: t.Type[T]) -> T | hikari.UndefinedType:
        """Get a type dependency for this client.

        Parameters
        ----------
        type_ : t.Type[T]
            The type of the dependency.

        Returns
        -------
        T | hikari.UndefinedType
            The instance of the dependency, if it exists.
        """
        return self._injector.get_type_dependency(type_, default=hikari.UNDEFINED)

    @t.overload
    def inject_dependencies(self, func: t.Callable[P, T]) -> t.Callable[P, T]:
        ...

    @t.overload
    def inject_dependencies(self) -> t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
        ...

    def inject_dependencies(
        self, func: t.Callable[P, T] | None = None
    ) -> t.Callable[P, T] | t.Callable[[t.Callable[P, T]], t.Callable[P, T]]:
        """Decorator to inject dependencies into the decorated function.

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

        def decorator(func: t.Callable[P, T]) -> t.Callable[P, T]:
            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def decorator_async(*args: P.args, **kwargs: P.kwargs) -> T:
                    return await self.injector.call_with_async_di(func, *args, **kwargs)

                return decorator_async  # pyright: ignore reportGeneralTypeIssues
            else:

                @functools.wraps(func)
                def decorator_inner(*args: P.args, **kwargs: P.kwargs) -> T:
                    return self.injector.call_with_di(func, *args, **kwargs)

                return decorator_inner

        if func is not None:
            return decorator(func)

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
        guild : hikari.SnowflakeishOr[hikari.PartialGuild] | None
            The guild to purge commands from
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
