from __future__ import annotations

import abc
import asyncio
import inspect
import typing as t

import attr
import hikari

from arc.abc.error_handler import HasErrorHandler
from arc.abc.hookable import Hookable, HookResult
from arc.abc.option import OptionBase
from arc.context import AutodeferMode
from arc.internal.types import (
    BuilderT,
    ClientT,
    CommandCallbackT,
    ErrorHandlerCallbackT,
    HookT,
    PostHookT,
    ResponseBuilderT,
)

if t.TYPE_CHECKING:
    from arc.abc.plugin import PluginBase
    from arc.context import Context


class CommandProto(t.Protocol):
    """A protocol for any command-like object. This includes commands, groups, subgroups, and subcommands."""

    name: str
    """The name of the command."""
    name_localizations: t.Mapping[hikari.Locale, str]
    """The name of the command in different locales."""

    @property
    @abc.abstractmethod
    def command_type(self) -> hikari.CommandType:
        """The type of command this object represents."""

    @property
    @abc.abstractmethod
    def qualified_name(self) -> t.Sequence[str]:
        """The fully qualified name of this command."""


class CallableCommandProto(t.Protocol[ClientT]):
    """A protocol for any command-like object that can be called directly. This includes commands and subcommands."""

    name: str
    """The name of the command."""
    name_localizations: t.Mapping[hikari.Locale, str]
    """The name of the command in different locales."""
    callback: CommandCallbackT[ClientT]

    @property
    @abc.abstractmethod
    def command_type(self) -> hikari.CommandType:
        """The type of command this object represents."""

    @property
    @abc.abstractmethod
    def qualified_name(self) -> t.Sequence[str]:
        """The fully qualified name of this command."""

    @abc.abstractmethod
    async def __call__(self, ctx: Context[ClientT], *args: t.Any, **kwargs: t.Any) -> None:
        """Call the callback of the command with the given context and arguments.

        Parameters
        ----------
        ctx : ContextT
            The context to invoke this command with.
        args : tuple[Any]
            The positional arguments to pass to the callback.
        kwargs : dict[str, Any]
            The keyword arguments to pass to the callback.
        """

    @abc.abstractmethod
    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> None | asyncio.Future[ResponseBuilderT]:
        """Invoke this command with the given context.

        Parameters
        ----------
        interaction : hikari.CommandInteraction
            The interaction to invoke this command with.
        args : tuple[Any]
            The positional arguments to pass to the callback.
        kwargs : dict[str, Any]
            The keyword arguments to pass to the callback.

        Returns
        -------
        None | asyncio.Future[ResponseBuilderT]
            If this is a REST client, returns the response builder.

        Raises
        ------
        RuntimeError
            If this command has not been added to a client.
        """

    @abc.abstractmethod
    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        ...

    def _resolve_hooks(self) -> t.Sequence[HookT[ClientT]]:
        """Resolve all pre-execution hooks that apply to this object."""
        ...

    def _resolve_post_hooks(self) -> t.Sequence[PostHookT[ClientT]]:
        """Resolve all post-execution hooks that apply to this object."""
        ...


@attr.define(slots=True, kw_only=True)
class CommandBase(HasErrorHandler[ClientT], Hookable[ClientT], t.Generic[ClientT, BuilderT]):
    """An abstract base class for all application commands."""

    name: str
    """The name of this command."""

    _client: ClientT | None = attr.field(init=False, default=None)
    """The client that is handling this command."""

    _plugin: PluginBase[ClientT] | None = attr.field(init=False, default=None)
    """The plugin that this command belongs to, if any."""

    guilds: hikari.UndefinedOr[t.Sequence[hikari.Snowflake]] = hikari.UNDEFINED
    """The guilds this command is available in."""

    autodefer: AutodeferMode = AutodeferMode.ON
    """If ON, this command will be automatically deferred if it takes longer than 2 seconds to respond."""

    is_dm_enabled: bool = True
    """Whether this command is enabled in DMs."""

    default_permissions: hikari.UndefinedOr[hikari.Permissions] = hikari.UNDEFINED
    """The default permissions for this command.
    Keep in mind that guild administrators can change this, it should only be used to provide safe defaults."""

    name_localizations: t.Mapping[hikari.Locale, str] = attr.field(factory=dict)
    """The localizations for this command's name."""

    is_nsfw: bool = False
    """Whether this command is NSFW. If true, the command will only be available in NSFW channels."""

    _instances: dict[hikari.Snowflake | None, hikari.PartialCommand] = attr.field(factory=dict)
    """A mapping of guild IDs to command instances. None corresponds to the global instance, if any."""

    _error_handler: ErrorHandlerCallbackT[ClientT] | None = attr.field(init=False, default=None)

    _hooks: list[HookT[ClientT]] = attr.field(init=False, factory=list)

    _post_hooks: list[PostHookT[ClientT]] = attr.field(init=False, factory=list)

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this command."""
        return self._error_handler

    @property
    def hooks(self) -> t.MutableSequence[HookT[ClientT]]:
        """The pre-execution hooks for this command."""
        return self._hooks

    @property
    def post_hooks(self) -> t.MutableSequence[PostHookT[ClientT]]:
        """The post-execution hooks for this command."""
        return self._post_hooks

    @property
    @abc.abstractmethod
    def command_type(self) -> hikari.CommandType:
        """The type of command this object represents."""

    @property
    @abc.abstractmethod
    def qualified_name(self) -> t.Sequence[str]:
        """The fully qualified name of this command."""

    @property
    def client(self) -> ClientT:
        """The client that is handling this command."""
        if self._client is None:
            raise RuntimeError(
                f"Command '{self.qualified_name}' was not included in a client, '{type(self).__name__}.client' cannot be accessed until it is included in a client."
            )
        return self._client

    @property
    def plugin(self) -> PluginBase[ClientT] | None:
        """The plugin that this command belongs to, if any."""
        return self._plugin

    def _register_instance(
        self, instance: hikari.PartialCommand, guild: hikari.SnowflakeishOr[hikari.PartialGuild] | None = None
    ) -> None:
        self._instances[hikari.Snowflake(guild) if guild else None] = instance

    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        try:
            if self.error_handler is not None:
                await self.error_handler(ctx, exc)
            else:
                raise exc
        except Exception as exc:
            if self.plugin:
                await self.plugin._handle_exception(ctx, exc)
            else:
                await self.client._on_error(ctx, exc)

    def _resolve_hooks(self) -> list[HookT[ClientT]]:
        plugin_hooks = self.plugin._resolve_hooks() if self.plugin else []
        return self.client._hooks + plugin_hooks + self._hooks

    def _resolve_post_hooks(self) -> list[PostHookT[ClientT]]:
        plugin_hooks = self.plugin._resolve_post_hooks() if self.plugin else []
        return self.client._post_hooks + plugin_hooks + self._post_hooks

    async def publish(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild] | None = None) -> hikari.PartialCommand:
        """Publish this command to the given guild, or globally if no guild is provided.

        Parameters
        ----------
        guild : hikari.Snowflakeish | None
            The guild to publish this command to. If None, publish globally.

        Returns
        -------
        hikari.PartialCommand
            The published command.
        """
        if self.client.application is None:
            raise RuntimeError("Cannot publish command without a client.")

        kwargs = self._to_dict()

        if self.command_type is hikari.CommandType.SLASH:
            created = await self.client.app.rest.create_slash_command(self.client.application, **kwargs)
        else:
            created = await self.client.app.rest.create_context_menu_command(
                self.client.application, type=self.command_type, **kwargs
            )

        self._instances[hikari.Snowflake(guild) if guild else None] = created

        return created

    async def unpublish(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild] | None = None) -> None:
        """Unpublish this command from the given guild, or globally if no guild is provided.

        Parameters
        ----------
        guild : hikari.Snowflakeish | None
            The guild to unpublish this command from. If None, unpublish globally.
        """
        if command := self._instances.pop(hikari.Snowflake(guild) if guild else None, None):
            await command.delete()

    @abc.abstractmethod
    def _get_context(
        self, interaction: hikari.CommandInteraction, command: CallableCommandProto[ClientT]
    ) -> Context[ClientT]:
        """Create a context object from an interaction."""

    @abc.abstractmethod
    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> None | asyncio.Future[ResponseBuilderT]:
        """Invoke this command with the given interaction.

        Parameters
        ----------
        interaction : hikari.CommandInteraction
            The interaction to invoke this command with.
        args : tuple[Any]
            The positional arguments to pass to the callback.
        kwargs : dict[str, Any]
            The keyword arguments to pass to the callback.

        Returns
        -------
        None | asyncio.Future[ResponseBuilderT]
            If this is a REST client, returns the response builder.

        Raises
        ------
        RuntimeError
            If this command has not been added to a client.
        """

    def _to_dict(self) -> dict[str, t.Any]:
        return {
            "name": self.name,
            "nsfw": self.is_nsfw,
            "default_member_permissions": self.default_permissions,
            "name_localizations": self.name_localizations,
            "dm_enabled": self.is_dm_enabled,
        }

    @abc.abstractmethod
    def _build(self) -> BuilderT:
        """Create a builder out of this command."""

    def _client_include_hook(self, client: ClientT) -> None:
        """Called when the client requests the command be added to it."""
        self._client = client
        self.client._add_command(self)

    def _client_remove_hook(self, client: ClientT) -> None:
        """Called when the client requests the command be removed from it."""
        self._client = None
        self.client._remove_command(self)

    def _plugin_include_hook(self, plugin: PluginBase[ClientT]) -> None:
        """Called when the plugin requests the command be added to it."""
        self._plugin = plugin
        self._plugin._add_command(self)

    async def _handle_pre_hooks(self, command: CallableCommandProto[ClientT], ctx: Context[ClientT]) -> bool:
        """Handle all pre-execution hooks for a command.

        Returns
        -------
        bool
            Whether the command should be aborted.
        """
        aborted = False
        try:
            hooks = command._resolve_hooks()
            for hook in hooks:
                if inspect.iscoroutinefunction(hook):
                    res = await hook(ctx)
                else:
                    res = hook(ctx)

                res = t.cast(HookResult | None, res)

                if res and res._abort:
                    aborted = True
        except Exception as e:
            aborted = True
            await command._handle_exception(ctx, e)

        return aborted

    async def _handle_post_hooks(self, command: CallableCommandProto[ClientT], ctx: Context[ClientT]) -> None:
        """Handle all post-execution hooks for a command."""
        try:
            post_hooks = command._resolve_post_hooks()
            for hook in post_hooks:
                if inspect.iscoroutinefunction(hook):
                    await hook(ctx)
                else:
                    hook(ctx)
        except Exception as e:
            await command._handle_exception(ctx, e)

    async def _handle_callback(
        self, command: CallableCommandProto[ClientT], ctx: Context[ClientT], *args: t.Any, **kwargs: t.Any
    ) -> None:
        """Handle the callback of a command. Invoke all hooks and the callback, and handle any exceptions."""
        # If hook aborted, stop invocation
        if await self._handle_pre_hooks(command, ctx):
            return

        try:
            await self.client.injector.call_with_async_di(command.callback, ctx, *args, **kwargs)
        except Exception as e:
            ctx._has_command_failed = True
            await command._handle_exception(ctx, e)
        finally:
            await self._handle_post_hooks(command, ctx)


@attr.define(slots=True, kw_only=True)
class CallableCommandBase(CommandBase[ClientT, BuilderT]):
    """A command that can be called directly. Note that this does not include subcommands, as those are options."""

    callback: CommandCallbackT[ClientT]
    """The callback to invoke when this command is called."""

    _invoke_task: asyncio.Task[t.Any] | None = attr.field(init=False, default=None)

    async def __call__(self, ctx: Context[ClientT], *args: t.Any, **kwargs: t.Any) -> None:
        await self.callback(ctx, *args, **kwargs)

    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> None | asyncio.Future[ResponseBuilderT]:
        ctx = self._get_context(interaction, self)
        if self.autodefer.should_autodefer:
            ctx._start_autodefer(self.autodefer)
        self._invoke_task = asyncio.create_task(self._handle_callback(self, ctx, *args, **kwargs))
        if self.client.is_rest:
            return ctx._resp_builder


ParentT = t.TypeVar("ParentT")


class SubCommandBase(OptionBase[ClientT], HasErrorHandler[ClientT], Hookable[ClientT], t.Generic[ClientT, ParentT]):
    """An abstract base class for all slash subcommands and subgroups."""

    _error_handler: ErrorHandlerCallbackT[ClientT] | None = attr.field(default=None, init=False)

    _hooks: list[HookT[ClientT]] = attr.field(factory=list, init=False)

    _post_hooks: list[PostHookT[ClientT]] = attr.field(factory=list, init=False)

    parent: ParentT | None = attr.field(default=None, init=False)
    """The parent of this subcommand or subgroup."""

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this object."""
        return self._error_handler

    @property
    def hooks(self) -> t.MutableSequence[HookT[ClientT]]:
        """The pre-execution hooks for this object."""
        return self._hooks

    @property
    def post_hooks(self) -> t.MutableSequence[PostHookT[ClientT]]:
        """The post-execution hooks for this object."""
        return self._post_hooks
