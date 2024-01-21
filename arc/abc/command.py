from __future__ import annotations

import abc
import asyncio
import inspect
import typing as t

import attr
import hikari

from arc.abc.concurrency_limiting import ConcurrencyLimiterProto, HasConcurrencyLimiter
from arc.abc.error_handler import HasErrorHandler
from arc.abc.hookable import Hookable, HookResult
from arc.abc.limiter import LimiterProto
from arc.abc.option import OptionBase
from arc.context import AutodeferMode
from arc.errors import GlobalCommandPublishFailedError, MaxConcurrencyReachedError
from arc.internal.types import (
    BuilderT,
    ClientT,
    CommandCallbackT,
    ErrorHandlerCallbackT,
    HookT,
    PostHookT,
    ResponseBuilderT,
)
from arc.locale import CommandLocaleRequest

if t.TYPE_CHECKING:
    import typing_extensions as te

    from arc.abc.plugin import PluginBase
    from arc.context.base import Context


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

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        """The display name of this command. This is what is shown in the Discord client.

        !!! note
            Slash commands can also be mentioned, see [SlashCommand.make_mention][arc.command.SlashCommand.make_mention].
        """


class CallableCommandProto(CommandProto, t.Protocol[ClientT]):
    """A protocol for any command-like object that can be called directly.

    This includes commands and subcommands, but not groups or subgroups.
    """

    name: str
    """The name of the command."""
    name_localizations: t.Mapping[hikari.Locale, str]
    """The name of the command in different locales."""

    callback: CommandCallbackT[ClientT]
    """The callback to invoke when this command is called."""

    @property
    @abc.abstractmethod
    def command_type(self) -> hikari.CommandType:
        """The type of command this object represents."""

    @property
    @abc.abstractmethod
    def qualified_name(self) -> t.Sequence[str]:
        """The fully qualified name of this command."""

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        """The display name of this command. This is what is shown in the Discord client.

        !!! note
            Slash commands can also be mentioned, see [SlashCommand.make_mention][arc.command.SlashCommand.make_mention].
        """

    @property
    @abc.abstractmethod
    def hooks(self) -> t.MutableSequence[HookT[ClientT]]:
        """The pre-execution hooks for this command."""

    @property
    @abc.abstractmethod
    def post_hooks(self) -> t.MutableSequence[PostHookT[ClientT]]:
        """The post-execution hooks for this command."""

    @abc.abstractmethod
    def reset_all_limiters(self, context: Context[ClientT]) -> None:
        """Reset all limiter hooks for this command.

        Parameters
        ----------
        context : Context
            The context to reset the limiters for.
        """

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
        """Handle an exception that occurred while invoking this command.

        Parameters
        ----------
        ctx : Context
            The context that the exception occurred in.
        exc : Exception
            The exception that occurred.
        """

    @abc.abstractmethod
    def _resolve_hooks(self) -> t.Sequence[HookT[ClientT]]:
        """Resolve all pre-execution hooks that apply to this object."""

    @abc.abstractmethod
    def _resolve_post_hooks(self) -> t.Sequence[PostHookT[ClientT]]:
        """Resolve all post-execution hooks that apply to this object."""

    @abc.abstractmethod
    def _resolve_concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """Resolve the concurrency limiter for this object."""


@t.final
@attr.define(slots=True, kw_only=True, weakref_slot=False)
class _CommandSettings:
    """All the command settings that need to propagate and be inherited."""

    autodefer: AutodeferMode | hikari.UndefinedType
    default_permissions: hikari.Permissions | hikari.UndefinedType
    is_nsfw: bool | hikari.UndefinedType
    is_dm_enabled: bool | hikari.UndefinedType

    def apply(self, other: te.Self) -> te.Self:
        """Apply 'other' to this, copying all the non-undefined settings to it."""
        return type(self)(
            autodefer=other.autodefer if other.autodefer is not hikari.UNDEFINED else self.autodefer,
            default_permissions=other.default_permissions
            if other.default_permissions is not hikari.UNDEFINED
            else self.default_permissions,
            is_nsfw=other.is_nsfw if other.is_nsfw is not hikari.UNDEFINED else self.is_nsfw,
            is_dm_enabled=other.is_dm_enabled if other.is_dm_enabled is not hikari.UNDEFINED else self.is_dm_enabled,
        )

    @classmethod
    def default(cls) -> te.Self:
        """Get the default command settings."""
        return cls(autodefer=AutodeferMode.ON, default_permissions=hikari.UNDEFINED, is_nsfw=False, is_dm_enabled=True)


@attr.define(slots=True, kw_only=True)
class CommandBase(
    HasErrorHandler[ClientT], Hookable[ClientT], HasConcurrencyLimiter[ClientT], t.Generic[ClientT, BuilderT]
):
    """An abstract base class for all application commands.

    This notably does not include subcommands & subgroups as those are in reality options.
    """

    name: str
    """The name of this command."""

    guilds: t.Sequence[hikari.Snowflake] | hikari.UndefinedType = hikari.UNDEFINED
    """The guilds this command is available in."""

    _autodefer: AutodeferMode | hikari.UndefinedType = attr.field(default=hikari.UNDEFINED, alias="autodefer")
    """If ON, this command will be automatically deferred if it takes longer than 2 seconds to respond."""

    _is_dm_enabled: bool | hikari.UndefinedType = attr.field(default=hikari.UNDEFINED, alias="is_dm_enabled")
    """Whether this command is enabled in DMs."""

    _default_permissions: hikari.Permissions | hikari.UndefinedType = attr.field(
        default=hikari.UNDEFINED, alias="default_permissions"
    )
    """The default permissions for this command.
    Keep in mind that guild administrators can change this, it should only be used to provide safe defaults."""

    _is_nsfw: bool | hikari.UndefinedType = attr.field(default=hikari.UNDEFINED, alias="is_nsfw")
    """Whether this command is NSFW. If true, the command will only be available in NSFW channels."""

    name_localizations: t.Mapping[hikari.Locale, str] = attr.field(factory=dict)
    """The localizations for this command's name."""

    _instances: dict[hikari.Snowflake | None, hikari.PartialCommand] = attr.field(factory=dict)
    """A mapping of guild IDs to command instances. None corresponds to the global instance, if any."""

    _client: ClientT | None = attr.field(init=False, default=None)
    """The client that is handling this command."""

    _plugin: PluginBase[ClientT] | None = attr.field(init=False, default=None)
    """The plugin that this command belongs to, if any."""

    _error_handler: ErrorHandlerCallbackT[ClientT] | None = attr.field(init=False, default=None)
    """The error handler for this command."""

    _concurrency_limiter: ConcurrencyLimiterProto[ClientT] | None = attr.field(init=False, default=None)
    """The concurrency limiter for this command."""

    _hooks: list[HookT[ClientT]] = attr.field(init=False, factory=list)
    """The pre-execution hooks for this command."""

    _post_hooks: list[PostHookT[ClientT]] = attr.field(init=False, factory=list)
    """The post-execution hooks for this command."""

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this command."""
        return self._error_handler

    @error_handler.setter
    def error_handler(self, callback: ErrorHandlerCallbackT[ClientT] | None) -> None:
        """Set the error handler for this command."""
        self._error_handler = callback

    @property
    def concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """The concurrency limiter for this command."""
        return self._concurrency_limiter

    @concurrency_limiter.setter
    def concurrency_limiter(self, limiter: ConcurrencyLimiterProto[ClientT] | None) -> None:
        """Set the concurrency limiter for this command."""
        self._concurrency_limiter = limiter

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
                f"Command '{self.display_name}' was not included in a client, '{type(self).__name__}.client' cannot be accessed until it is included in a client."
            )
        return self._client

    @property
    def plugin(self) -> PluginBase[ClientT] | None:
        """The plugin that this command belongs to, if any."""
        return self._plugin

    @property
    def autodefer(self) -> AutodeferMode:
        """The resolved autodefer configuration for this command."""
        settings = self._resolve_settings()
        return settings.autodefer if settings.autodefer is not hikari.UNDEFINED else AutodeferMode.ON

    @property
    def is_dm_enabled(self) -> bool:
        """Whether this command is enabled in DMs."""
        settings = self._resolve_settings()
        return settings.is_dm_enabled if settings.is_dm_enabled is not hikari.UNDEFINED else True

    @property
    def default_permissions(self) -> hikari.Permissions | hikari.UndefinedType:
        """The resolved default permissions for this command."""
        return self._resolve_settings().default_permissions

    @property
    def is_nsfw(self) -> bool:
        """Whether this command is NSFW. If true, the command will only be available in NSFW channels."""
        settings = self._resolve_settings()
        return settings.is_nsfw if settings.is_nsfw is not hikari.UNDEFINED else False

    @property
    def instances(self) -> t.Mapping[hikari.Snowflake | None, hikari.PartialCommand]:
        """A mapping of guild IDs to command instances. None corresponds to the global instance, if any."""
        return self._instances

    @property
    def display_name(self) -> str:
        """The display name of this command. This is what is shown in the Discord client.

        !!! note
            Slash commands can also be mentioned, see [SlashCommand.make_mention][arc.command.SlashCommand.make_mention].
        """
        return self.name

    def _register_instance(
        self,
        instance: hikari.PartialCommand,
        guild: hikari.SnowflakeishOr[hikari.PartialGuild] | hikari.UndefinedType = hikari.UNDEFINED,
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

    def _resolve_settings(self) -> _CommandSettings:
        """Resolve all settings that apply to this command."""
        if self._plugin:
            settings = self._plugin._resolve_settings()
        elif self._client:
            settings = self._client._cmd_settings
        else:
            settings = _CommandSettings.default()

        return settings.apply(
            _CommandSettings(
                autodefer=self._autodefer,
                default_permissions=self._default_permissions,
                is_nsfw=self._is_nsfw,
                is_dm_enabled=self._is_dm_enabled,
            )
        )

    def _resolve_concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """Resolve the concurrency limiter for this command."""
        if self._concurrency_limiter is not None:
            return self._concurrency_limiter

        if self._plugin:
            return self._plugin._resolve_concurrency_limiter()

        if self._client:
            return self._client._concurrency_limiter

        return None

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
        try:
            if self.command_type is hikari.CommandType.SLASH:
                created = await self.client.app.rest.create_slash_command(self.client.application, **kwargs)
            else:
                created = await self.client.app.rest.create_context_menu_command(
                    self.client.application, type=self.command_type, **kwargs
                )
        except Exception as e:
            raise GlobalCommandPublishFailedError(self, f"Failed to publish command '{self.display_name}'") from e

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
    def _build(self, id: hikari.Snowflake | hikari.UndefinedType = hikari.UNDEFINED) -> BuilderT:
        """Create a builder out of this command.

        Parameters
        ----------
        id : hikari.Snowflake | hikari.UndefinedType
            The ID of the command, if it already exists.
            If provided, this will edit the existing command, otherwise it will create a new one.
        """

    def _client_include_hook(self, client: ClientT) -> None:
        """Called when the client requests the command be added to it."""
        self._client = client
        self.client._add_command(self)

    def _client_remove_hook(self, client: ClientT) -> None:
        """Called when the client requests the command be removed from it."""
        self.client._remove_command(self)
        self._client = None

    def _plugin_include_hook(self, plugin: PluginBase[ClientT]) -> None:
        """Called when the plugin requests the command be added to it."""
        self._plugin = plugin
        self._plugin._add_command(self)

    def _request_command_locale(self) -> None:
        """Request the locale for this command."""
        if self.name_localizations or self._client is None:
            return

        if not self._client._provided_locales or not self._client._command_locale_provider:
            return

        name_locales: dict[hikari.Locale, str] = {}

        for locale in self._client._provided_locales:
            request = CommandLocaleRequest(self, locale, self.name)
            resp = self._client._command_locale_provider(request)

            if resp.name is not None:
                name_locales[locale] = resp.name

        self.name_localizations = name_locales

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
                res = hook(ctx)

                if inspect.isawaitable(res):
                    res = await res

                res = t.cast(HookResult | None, res)

                if res and res._abort:
                    aborted = True
        except Exception as e:
            aborted = True
            await command._handle_exception(ctx, e)

        return aborted

    async def _handle_post_hooks(self, command: CallableCommandProto[ClientT], ctx: Context[ClientT]) -> None:
        """Handle all post-execution hooks for a command, and release the concurrency limiter if applicable."""
        try:
            post_hooks = command._resolve_post_hooks()
            for hook in post_hooks:
                if inspect.iscoroutinefunction(hook):
                    await hook(ctx)
                else:
                    hook(ctx)
        except Exception as e:
            await command._handle_exception(ctx, e)
        finally:
            if (limiter := command._resolve_concurrency_limiter()) is not None:
                limiter.release(ctx)

    async def _handle_callback(
        self, command: CallableCommandProto[ClientT], ctx: Context[ClientT], *args: t.Any, **kwargs: t.Any
    ) -> None:
        """Handle the callback of a command. Invoke all hooks and the callback, and handle any exceptions."""
        # If hook aborted, stop invocation

        max_concurrency = command._resolve_concurrency_limiter()

        if max_concurrency is not None and max_concurrency.is_exhausted(ctx):
            return await command._handle_exception(
                ctx, MaxConcurrencyReachedError(max_concurrency, max_concurrency.limit)
            )

        try:
            if max_concurrency is not None:
                await max_concurrency.acquire(ctx)

            if await self._handle_pre_hooks(command, ctx):
                return

            await self.client.injector.call_with_async_di(command.callback, ctx, *args, **kwargs)

        except Exception as e:
            ctx._has_command_failed = True
            await command._handle_exception(ctx, e)
        finally:
            # This also releases the concurrency limiter
            await self._handle_post_hooks(command, ctx)


@attr.define(slots=True, kw_only=True)
class CallableCommandBase(CommandBase[ClientT, BuilderT], CallableCommandProto[ClientT]):
    """A top-level command that can be called directly. Note that this does not include subcommands, as those are options."""

    callback: CommandCallbackT[ClientT]
    """The callback to invoke when this command is called."""

    _invoke_task: asyncio.Task[t.Any] | None = attr.field(init=False, default=None, repr=False)

    def reset_all_limiters(self, context: Context[ClientT]) -> None:
        """Reset all limiter hooks for this command.

        Parameters
        ----------
        context : Context
            The context to reset the limiters for.
        """
        limiters: t.Generator[LimiterProto[ClientT], None, None] = (
            lim for lim in self._resolve_hooks() if isinstance(lim, LimiterProto)
        )
        for limiter in limiters:
            limiter.reset(context)

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


@attr.define(slots=True, kw_only=True)
class SubCommandBase(
    OptionBase[ClientT],
    HasErrorHandler[ClientT],
    Hookable[ClientT],
    HasConcurrencyLimiter[ClientT],
    t.Generic[ClientT, ParentT],
):
    """An abstract base class for all slash subcommands and subgroups."""

    _error_handler: ErrorHandlerCallbackT[ClientT] | None = attr.field(default=None, init=False)

    _concurrency_limiter: ConcurrencyLimiterProto[ClientT] | None = attr.field(default=None, init=False)

    _hooks: list[HookT[ClientT]] = attr.field(factory=list, init=False)

    _post_hooks: list[PostHookT[ClientT]] = attr.field(factory=list, init=False)

    _parent: ParentT | None = attr.field(default=None, init=False, alias="parent")
    """The parent of this subcommand or subgroup."""

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        """The display name of this command. This is what is shown in the Discord client.

        !!! note
            Slash commands can also be mentioned, see [SlashCommand.make_mention][arc.command.SlashCommand.make_mention].
        """

    @property
    def error_handler(self) -> ErrorHandlerCallbackT[ClientT] | None:
        """The error handler for this object."""
        return self._error_handler

    @error_handler.setter
    def error_handler(self, callback: ErrorHandlerCallbackT[ClientT] | None) -> None:
        """Set the error handler for this object."""
        self._error_handler = callback

    @property
    def concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        """The concurrency limiter for this object."""
        return self._concurrency_limiter

    @concurrency_limiter.setter
    def concurrency_limiter(self, limiter: ConcurrencyLimiterProto[ClientT] | None) -> None:
        """Set the concurrency limiter for this object."""
        self._concurrency_limiter = limiter

    @property
    def hooks(self) -> t.MutableSequence[HookT[ClientT]]:
        """The pre-execution hooks for this object."""
        return self._hooks

    @property
    def post_hooks(self) -> t.MutableSequence[PostHookT[ClientT]]:
        """The post-execution hooks for this object."""
        return self._post_hooks

    @property
    def parent(self) -> ParentT:
        """The parent of this subcommand or subgroup."""
        if self._parent is None:
            raise RuntimeError(
                f"Subcommand '{self.name}' was not included in a parent, '{type(self).__name__}.parent' cannot be accessed until it is included in a parent."
            )
        return self._parent

    def reset_all_limiters(self, context: Context[ClientT]) -> None:
        """Reset all limiter hooks for this command.

        Parameters
        ----------
        context : Context
            The context to reset the limiters for.
        """
        limiters: t.Generator[LimiterProto[ClientT], None, None] = (
            lim for lim in self._resolve_hooks() if isinstance(lim, LimiterProto)
        )
        for limiter in limiters:
            limiter.reset(context)


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
