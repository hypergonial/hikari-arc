from __future__ import annotations

import asyncio
import typing as t

import attr
import hikari

from arc.abc.command import CallableCommandBase, CallableCommandProto, CommandBase, SubCommandBase, _CommandSettings
from arc.abc.option import OptionType, OptionWithChoices
from arc.context import AutocompleteData, AutodeferMode, Context
from arc.errors import AutocompleteError, CommandInvokeError
from arc.internal.options import resolve_options
from arc.internal.sigparse import parse_command_signature
from arc.internal.types import ClientT, CommandCallbackT, HookT, PostHookT, ResponseBuilderT, SlashCommandLike
from arc.locale import CommandLocaleRequest, LocaleResponse

if t.TYPE_CHECKING:
    from asyncio.futures import Future

    from arc.abc.client import Client
    from arc.abc.command import CommandProto
    from arc.abc.concurrency_limiting import ConcurrencyLimiterProto
    from arc.abc.option import CommandOptionBase
    from arc.abc.plugin import PluginBase

__all__ = (
    "SlashCommandLike",
    "SlashCommand",
    "SlashGroup",
    "SlashSubCommand",
    "SlashSubGroup",
    "slash_command",
    "slash_subcommand",
)


def _choices_to_builders(
    choices: t.Sequence[hikari.api.AutocompleteChoiceBuilder] | t.Sequence[t.Any],
) -> t.Sequence[hikari.api.AutocompleteChoiceBuilder]:
    """Convert a sequence of choices to a sequence of choice builders."""
    return [
        (
            hikari.impl.AutocompleteChoiceBuilder(str(e), e)
            if not isinstance(e, hikari.api.AutocompleteChoiceBuilder)
            else e
        )
        for e in choices
    ]


@attr.define(slots=True, kw_only=True)
class SlashCommand(CallableCommandBase[ClientT, hikari.api.SlashCommandBuilder]):
    """A slash command outside of any group."""

    description: str = "No description provided."
    """The description of this slash command."""

    description_localizations: t.Mapping[hikari.Locale, str] = attr.field(factory=dict)
    """The localizations for this command's description."""

    options: dict[str, CommandOptionBase[t.Any, ClientT, t.Any]] = attr.field(factory=dict)
    """The options of this slash command."""

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def qualified_name(self) -> t.Sequence[str]:
        return (self.name,)

    @property
    def display_name(self) -> str:
        """The display name of this command."""
        return f"/{self.name}"

    def _get_context(
        self, interaction: hikari.CommandInteraction, command: CallableCommandProto[ClientT]
    ) -> Context[ClientT]:
        assert self.client is not None

        if interaction.command_type is not hikari.CommandType.SLASH:
            raise ValueError(f"Expected slash command, got {interaction.command_type}")

        ctx = Context(self.client, command, interaction)
        ctx._options = interaction.options
        return ctx

    def _to_dict(self) -> dict[str, t.Any]:
        sorted_options = sorted(self.options.values(), key=lambda option: option.is_required, reverse=True)
        payload = {
            **super()._to_dict(),
            "description": self.description,
            "description_localizations": self.description_localizations,
        }
        if sorted_options:
            payload["options"] = [option.to_command_option() for option in sorted_options]
        return payload

    def _build(self, id: hikari.Snowflake | hikari.UndefinedType = hikari.UNDEFINED) -> hikari.api.SlashCommandBuilder:
        return hikari.impl.SlashCommandBuilder(
            name=self.name,
            description=self.description,
            id=id,
            options=[option.to_command_option() for option in self.options.values()],
            default_member_permissions=self.default_permissions,
            is_dm_enabled=self.is_dm_enabled,
            is_nsfw=self.is_nsfw,
            name_localizations=self.name_localizations,  # pyright: ignore reportGeneralTypeIssues
            description_localizations=self.description_localizations,  # pyright: ignore reportGeneralTypeIssues
        )

    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> Future[ResponseBuilderT] | None:
        if interaction.options:
            return await super().invoke(
                interaction,
                *args,
                **{**kwargs, **resolve_options(self.options, interaction.options, interaction.resolved)},
            )
        else:
            return await super().invoke(interaction, *args, **kwargs)

    def make_mention(self, *, guild: hikari.Snowflakeish | hikari.PartialGuild | None = None) -> str:
        """Make a slash mention for this command.

        Parameters
        ----------
        guild : hikari.SnowflakeishOr[hikari.PartialGuild] | None
            The guild the command is registered in. If None, the global command's ID is used.

        Returns
        -------
        str
            The slash command mention.

        Raises
        ------
        KeyError
            If the command has not been published in the given guild or globally.
        """
        instance = self._instances.get(hikari.Snowflake(guild) if guild else None)

        if instance is None:
            raise KeyError(f"Command '{self.display_name}' has not been published in the given scope.")

        return f"</{self.name}:{instance.id}>"

    async def _on_autocomplete(
        self, interaction: hikari.AutocompleteInteraction
    ) -> hikari.api.InteractionAutocompleteBuilder | None:
        opt = next((o for o in interaction.options if o.name in self.options and o.is_focused), None)

        if opt is None:
            raise ValueError(f"Slash command got unknown option to autocomplete: '{interaction.options[0]}'.")

        local_opt = self.options[opt.name]

        if not isinstance(local_opt, OptionWithChoices) or not local_opt.autocomplete_with:
            raise ValueError(
                f"Slash option got autocomplete interaction without autocomplete callback: '{local_opt.name}'."
            )

        choices = _choices_to_builders(
            await self.client.injector.call_with_async_di(
                local_opt.autocomplete_with,  # pyright: ignore reportGeneralTypeIssues
                AutocompleteData(
                    interaction=interaction, options=interaction.options, client=self.client, command=self
                ),
            )
        )

        if self.client.is_rest:
            return interaction.build_response(choices)

        await interaction.create_response(choices)

    def _request_command_locale(self) -> None:
        """Request the locale for this command."""
        if self.name_localizations or self.description_localizations or self._client is None:
            return

        if not self._client._provided_locales or not self._client._command_locale_provider:
            return

        name_locales: dict[hikari.Locale, str] = {}
        desc_locales: dict[hikari.Locale, str] = {}

        for locale in self._client._provided_locales:
            request = CommandLocaleRequest(self, locale, self.name)
            resp = self._client._command_locale_provider(request)

            assert isinstance(resp, LocaleResponse)

            if resp.name is not None and resp.description is not None:
                name_locales[locale] = resp.name
                desc_locales[locale] = resp.description

        self.name_localizations: t.Mapping[hikari.Locale, str] = name_locales
        self.description_localizations: t.Mapping[hikari.Locale, str] = desc_locales

        for option in self.options.values():
            option._request_option_locale(self._client, self)


@attr.define(slots=True, kw_only=True)
class SlashGroup(CommandBase[ClientT, hikari.api.SlashCommandBuilder]):
    """A group for slash subcommands and subgroups."""

    children: dict[str, SlashSubCommand[ClientT] | SlashSubGroup[ClientT]] = attr.field(factory=dict, init=False)
    """Subcommands and subgroups that belong to this group."""

    description: str = "No description provided."
    """The description of this slash group."""

    description_localizations: t.Mapping[hikari.Locale, str] = attr.field(factory=dict)
    """The localizations for this group's description."""

    _invoke_task: asyncio.Task[t.Any] | None = attr.field(init=False, default=None)

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def qualified_name(self) -> t.Sequence[str]:
        return (self.name,)

    @property
    def display_name(self) -> str:
        """The display name of this command."""
        return f"/{self.name}"

    def _to_dict(self) -> dict[str, t.Any]:
        payload = {
            **super()._to_dict(),
            "description": self.description,
            "description_localizations": self.description_localizations,
        }
        if self.children:
            payload["options"] = [subcmd.to_command_option() for subcmd in self.children.values()]
        return payload

    def _get_context(
        self, interaction: hikari.CommandInteraction, command: CallableCommandProto[ClientT]
    ) -> Context[ClientT]:
        assert self.client is not None

        if interaction.command_type is not hikari.CommandType.SLASH:
            raise ValueError(f"Expected slash command, got {interaction.command_type}")

        return Context(self.client, command, interaction)

    def _build(self, id: hikari.Snowflake | hikari.UndefinedType = hikari.UNDEFINED) -> hikari.api.SlashCommandBuilder:
        return hikari.impl.SlashCommandBuilder(
            name=self.name,
            description=self.description,
            id=id,
            options=[subcmd.to_command_option() for subcmd in self.children.values()],
            default_member_permissions=self.default_permissions,
            is_dm_enabled=self.is_dm_enabled,
            is_nsfw=self.is_nsfw,
            name_localizations=self.name_localizations,  # pyright: ignore reportGeneralTypeIssues
            description_localizations=self.description_localizations,  # pyright: ignore reportGeneralTypeIssues
        )

    async def _invoke_subcmd(
        self,
        subcommand: SlashSubCommand[ClientT],
        interaction: hikari.CommandInteraction,
        options: t.Sequence[hikari.CommandInteractionOption] | None = None,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> asyncio.Future[ResponseBuilderT] | None:
        """Invoke a subcommand."""
        ctx = self._get_context(interaction, subcommand)
        ctx._options = options

        if (autodefer := subcommand.autodefer) and autodefer.should_autodefer:
            ctx._start_autodefer(autodefer)

        self._invoke_task = asyncio.create_task(self._handle_callback(subcommand, ctx, *args, **kwargs))
        if self.client.is_rest:
            return ctx._resp_builder

    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> Future[ResponseBuilderT] | None:
        if interaction.options is None:
            raise CommandInvokeError("Cannot invoke slash group with empty options.")

        # Get first-order subcommand
        sub = next((o for o in interaction.options if o.name in self.children), None)

        if sub is None:
            raise CommandInvokeError(f"Slash group got unknown subcommand: '{interaction.options[0]}'.")

        subcmd = self.children[sub.name]

        # Invoke it if it has no options
        if sub.options is None:
            if not isinstance(subcmd, SlashSubCommand):
                raise CommandInvokeError(f"Slash group got subgroup without options: '{subcmd.name}'.")
            return await self._invoke_subcmd(subcmd, interaction, None, *args, **kwargs)

        # Resolve options and invoke if it does
        if isinstance(subcmd, SlashSubCommand):
            res = resolve_options(subcmd.options, sub.options, interaction.resolved)
            return await self._invoke_subcmd(subcmd, interaction, sub.options, *args, **{**kwargs, **res})

        # Get second-order subcommand
        subsub = next((o for o in sub.options if o.name in subcmd.children), None)

        if subsub is None:
            raise CommandInvokeError(f"Slash group got unknown subcommand: '{sub.options[0]}'.")

        subsubcmd = subcmd.children[subsub.name]

        # Invoke it if it has no options
        if subsub.options is None:
            return await self._invoke_subcmd(subsubcmd, interaction, None, *args, **kwargs)

        # Resolve options and invoke if it does
        res = resolve_options(subsubcmd.options, subsub.options, interaction.resolved)
        return await self._invoke_subcmd(subsubcmd, interaction, subsub.options, *args, **{**kwargs, **res})

    async def _on_autocomplete(
        self, interaction: hikari.AutocompleteInteraction
    ) -> hikari.api.InteractionAutocompleteBuilder | None:
        # First-order subcommand
        sub = next((o for o in interaction.options if o.name in self.children), None)

        if sub is None:
            raise AutocompleteError(f"Slash group got unknown subcommand to autocomplete: '{interaction.options[0]}'.")

        subcmd = self.children[sub.name]

        if sub.options is None:
            raise AutocompleteError(f"Slash group got subcommand without options: '{subcmd.name}'.")

        # If it is a first-order subcommand, get the option
        if isinstance(subcmd, SlashSubCommand):
            opts = sub.options
            opt = next(o for o in sub.options if o.name in subcmd.options and o.is_focused)
            local_opt = subcmd.options[opt.name]
        else:
            # Otherwise continue the conga-line
            subsub = next((o for o in sub.options if o.name in subcmd.children), None)

            if subsub is None:
                raise AutocompleteError(f"Slash subgroup got unknown subcommand to autocomplete: '{sub.options[0]}'.")

            if subsub.options is None:
                raise AutocompleteError(f"Slash subgroup got subcommand without options: '{subsub.name}'.")

            subsubcmd = subcmd.children[subsub.name]
            opts = subsub.options
            opt = next(o for o in subsub.options if o.name in subsubcmd.options and o.is_focused)
            local_opt = subsubcmd.options[opt.name]

        if not isinstance(local_opt, OptionWithChoices) or not local_opt.autocomplete_with:
            raise AutocompleteError(
                f"Slash option got autocomplete interaction without autocomplete callback: '{local_opt.name}'."
            )

        choices = _choices_to_builders(
            await self.client.injector.call_with_async_di(
                local_opt.autocomplete_with,  # pyright: ignore reportGeneralTypeIssues
                AutocompleteData(interaction=interaction, options=opts, client=self.client, command=self),
            )
        )

        if self.client.is_rest:
            return interaction.build_response(choices)

        await interaction.create_response(choices)

    def _request_command_locale(self) -> None:
        """Request the locale for this command."""
        if self.name_localizations or self.description_localizations or self._client is None:
            return

        if not self._client._provided_locales or not self._client._command_locale_provider:
            return

        name_locales: dict[hikari.Locale, str] = {}
        desc_locales: dict[hikari.Locale, str] = {}

        for locale in self._client._provided_locales:
            request = CommandLocaleRequest(self, locale, self.name)
            resp = self._client._command_locale_provider(request)

            if resp.name is not None and resp.description is not None:
                name_locales[locale] = resp.name
                desc_locales[locale] = resp.description

        self.name_localizations: t.Mapping[hikari.Locale, str] = name_locales
        self.description_localizations: t.Mapping[hikari.Locale, str] = desc_locales

        for sub in self.children.values():
            sub._request_option_locale(self._client, self)

    @t.overload
    def include(self) -> t.Callable[[SlashSubCommand[ClientT]], SlashSubCommand[ClientT]]:
        ...

    @t.overload
    def include(self, command: SlashSubCommand[ClientT]) -> SlashSubCommand[ClientT]:
        ...

    def include(
        self, command: SlashSubCommand[ClientT] | None = None
    ) -> SlashSubCommand[ClientT] | t.Callable[[SlashSubCommand[ClientT]], SlashSubCommand[ClientT]]:
        """Decorator to add a subcommand to this group."""

        def decorator(command: SlashSubCommand[ClientT]) -> SlashSubCommand[ClientT]:
            command._parent = self
            self.children[command.name] = command
            return command

        if command is not None:
            return decorator(command)

        return decorator

    def include_subgroup(
        self,
        name: str,
        description: str = "No description provided.",
        *,
        autodefer: AutodeferMode | bool | hikari.UndefinedType = hikari.UNDEFINED,
        name_localizations: t.Mapping[hikari.Locale, str] | None = None,
        description_localizations: t.Mapping[hikari.Locale, str] | None = None,
    ) -> SlashSubGroup[ClientT]:
        """Create a subgroup and add it to this group.

        Parameters
        ----------
        name : str
            The name of the subgroup.
        description : str
            The description of the subgroup
        autodefer : bool | AutodeferMode | hikari.UndefinedType
            If True, all commands in this subgroup will automatically defer if it is taking longer than 2 seconds to respond.
            If not provided, then this setting will be inherited from the parent.
        name_localizations : dict[hikari.Locale, str] | None
            Localizations for the name of the subgroup
        description_localizations : dict[hikari.Locale, str] | None
            Localizations for the description of the subgroup
        """
        group: SlashSubGroup[ClientT] = SlashSubGroup(
            name=name,
            description=description,
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            name_localizations=name_localizations or {},
            description_localizations=description_localizations or {},
        )
        group._parent = self
        self.children[name] = group
        return group


@attr.define(slots=True, kw_only=True)
class SlashSubGroup(SubCommandBase[ClientT, SlashGroup[ClientT]]):
    """A subgroup of a slash command group."""

    children: dict[str, SlashSubCommand[ClientT]] = attr.field(factory=dict, init=False)
    """Subcommands that belong to this subgroup."""

    _autodefer: AutodeferMode | hikari.UndefinedType = attr.field(default=hikari.UNDEFINED, alias="autodefer")
    """If True, this subcommand will automatically defer if it is taking longer than 2 seconds to respond.
    If undefined, then it will be inherited from the parent.
    """

    @property
    def option_type(self) -> OptionType:
        return OptionType.SUB_COMMAND_GROUP

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def qualified_name(self) -> t.Sequence[str]:
        return (self.parent.name, self.name)

    @property
    def display_name(self) -> str:
        return "/" + " ".join(self.qualified_name)

    @property
    def client(self) -> ClientT:
        """The client that includes this subgroup."""
        return self.parent.client

    @property
    def plugin(self) -> PluginBase[ClientT] | None:
        """The plugin that includes this subgroup."""
        return self.parent.plugin

    @property
    def autodefer(self) -> AutodeferMode:
        """The resolved autodefer configuration for this subcommand."""
        autodefer = self._resolve_settings().autodefer
        assert autodefer is not hikari.UNDEFINED
        return autodefer

    def _to_dict(self) -> dict[str, t.Any]:
        payload = super()._to_dict()
        if self.children:
            payload["options"] = [subcmd.to_command_option() for subcmd in self.children.values()]
        return payload

    def _resolve_settings(self) -> _CommandSettings:
        settings = self._parent._resolve_settings() if self._parent else _CommandSettings.default()

        return settings.apply(
            _CommandSettings(
                autodefer=self._autodefer,
                default_permissions=hikari.UNDEFINED,
                is_nsfw=hikari.UNDEFINED,
                is_dm_enabled=hikari.UNDEFINED,
            )
        )

    def _resolve_hooks(self) -> list[HookT[ClientT]]:
        assert self._parent is not None
        return self._parent._resolve_hooks() + self._hooks

    def _resolve_post_hooks(self) -> list[PostHookT[ClientT]]:
        assert self._parent is not None
        return self._parent._resolve_post_hooks() + self._post_hooks

    def _resolve_concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        assert self._parent is not None
        return self._parent._resolve_concurrency_limiter()

    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        try:
            if self.error_handler:
                await self.error_handler(ctx, exc)
            else:
                raise exc
        except Exception as e:
            assert self._parent is not None
            await self._parent._handle_exception(ctx, e)

    def _request_option_locale(self, client: Client[t.Any], command: CommandProto) -> None:
        super()._request_option_locale(client, command)

        for subcommand in self.children.values():
            subcommand._request_option_locale(client, command)

    @t.overload
    def include(self) -> t.Callable[[SlashSubCommand[ClientT]], SlashSubCommand[ClientT]]:
        ...

    @t.overload
    def include(self, command: SlashSubCommand[ClientT]) -> SlashSubCommand[ClientT]:
        ...

    def include(
        self, command: SlashSubCommand[ClientT] | None = None
    ) -> SlashSubCommand[ClientT] | t.Callable[[SlashSubCommand[ClientT]], SlashSubCommand[ClientT]]:
        """First-order decorator to add a subcommand to this group."""

        def decorator(command: SlashSubCommand[ClientT]) -> SlashSubCommand[ClientT]:
            command._parent = self
            self.children[command.name] = command
            return command

        if command is not None:
            return decorator(command)

        return decorator


@attr.define(slots=True, kw_only=True)
class SlashSubCommand(
    SubCommandBase[ClientT, SlashGroup[ClientT] | SlashSubGroup[ClientT]], CallableCommandProto[ClientT]
):
    """A subcommand of a slash command group."""

    callback: CommandCallbackT[ClientT]
    """The callback that will be invoked when this subcommand is invoked."""

    options: t.MutableMapping[str, CommandOptionBase[ClientT, t.Any, t.Any]] = attr.field(factory=dict)
    """The options of this subcommand."""

    _autodefer: AutodeferMode | hikari.UndefinedType = attr.field(default=hikari.UNDEFINED, alias="autodefer")
    """If True, this subcommand will automatically defer if it is taking longer than 2 seconds to respond.
    If undefined, then it will be inherited from the parent.
    """

    _invoke_task: asyncio.Task[t.Any] | None = attr.field(default=None, init=False)

    @property
    def root(self) -> SlashGroup[ClientT]:
        """The root group of this subcommand."""
        if self._parent is None:
            raise ValueError("Cannot get root of subcommand without parent.")

        if isinstance(self._parent, SlashSubGroup):
            if self._parent._parent is None:
                raise ValueError("Cannot get root of subcommand without parent.")

            return self._parent._parent

        return self._parent

    @property
    def qualified_name(self) -> t.Sequence[str]:
        if isinstance(self._parent, SlashSubGroup):
            return (self.root.name, self.parent.name, self.name)

        return (self.parent.name, self.name)

    @property
    def parent(self) -> SlashGroup[ClientT] | SlashSubGroup[ClientT]:
        """The parent of this subcommand."""
        if self._parent is None:
            raise ValueError("Cannot get parent of subcommand without parent.")
        return self._parent

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def option_type(self) -> OptionType:
        return OptionType.SUB_COMMAND

    @property
    def client(self) -> ClientT:
        """The client that includes this subcommand."""
        return self.root.client

    @property
    def plugin(self) -> PluginBase[ClientT] | None:
        """The plugin that includes this subcommand."""
        return self.root.plugin

    @property
    def autodefer(self) -> AutodeferMode:
        """The resolved autodefer configuration for this subcommand."""
        autodefer = self._resolve_settings().autodefer
        assert autodefer is not hikari.UNDEFINED
        return autodefer

    @property
    def display_name(self) -> str:
        return "/" + " ".join(self.qualified_name)

    def make_mention(self, guild: hikari.Snowflakeish | hikari.PartialGuild | None = None) -> str:
        """Make a slash mention for this command.

        Returns
        -------
        str
            The slash command mention.
        """
        instance = self.root._instances.get(hikari.Snowflake(guild) if guild else None)

        if instance is None:
            raise KeyError(f"Command '{self.display_name}' has not been published in the given scope.")

        return f"</{' '.join(self.qualified_name)}:{instance.id}>"

    def _resolve_settings(self) -> _CommandSettings:
        settings = self._parent._resolve_settings() if self._parent else _CommandSettings.default()

        return settings.apply(
            _CommandSettings(
                autodefer=self._autodefer,
                default_permissions=hikari.UNDEFINED,
                is_nsfw=hikari.UNDEFINED,
                is_dm_enabled=hikari.UNDEFINED,
            )
        )

    def _resolve_hooks(self) -> list[HookT[ClientT]]:
        assert self._parent is not None
        return self._parent._resolve_hooks() + self._hooks

    def _resolve_post_hooks(self) -> list[PostHookT[ClientT]]:
        assert self._parent is not None
        return self._parent._resolve_post_hooks() + self._post_hooks

    def _resolve_concurrency_limiter(self) -> ConcurrencyLimiterProto[ClientT] | None:
        assert self._parent is not None
        return self._parent._resolve_concurrency_limiter()

    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        try:
            if self.error_handler:
                await self.error_handler(ctx, exc)
            else:
                raise exc
        except Exception as e:
            assert self._parent is not None
            await self._parent._handle_exception(ctx, e)

    def _request_option_locale(self, client: Client[t.Any], command: CommandProto) -> None:
        super()._request_option_locale(client, command)

        for option in self.options.values():
            option._request_option_locale(client, command)

    async def __call__(self, ctx: Context[ClientT], *args: t.Any, **kwargs: t.Any) -> None:
        """Invoke this subcommand with the given context.

        Parameters
        ----------
        ctx : Context
            The context to invoke this subcommand with.
        args: list[t.Any]
            The positional arguments to pass to the callback.
        kwargs : dict[str, Any]
            The keyword arguments to pass to the callback.
        """
        await self.callback(ctx, *args, **kwargs)

    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> asyncio.Future[ResponseBuilderT] | None:
        return await self.root._invoke_subcmd(self, interaction, *args, **kwargs)

    def _to_dict(self) -> dict[str, t.Any]:
        payload = super()._to_dict()
        sorted_options = sorted(self.options.values(), key=lambda option: option.is_required, reverse=True)
        if sorted_options:
            payload["options"] = [option.to_command_option() for option in sorted_options]
        return payload


def slash_command(
    name: str,
    description: str = "No description provided.",
    *,
    guilds: t.Sequence[hikari.PartialGuild | hikari.Snowflakeish] | hikari.UndefinedType = hikari.UNDEFINED,
    is_dm_enabled: bool | hikari.UndefinedType = hikari.UNDEFINED,
    is_nsfw: bool | hikari.UndefinedType = hikari.UNDEFINED,
    autodefer: bool | AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED,
    default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
    name_localizations: t.Mapping[hikari.Locale, str] | None = None,
    description_localizations: t.Mapping[hikari.Locale, str] | None = None,
) -> t.Callable[[CommandCallbackT[ClientT]], SlashCommand[ClientT]]:
    """A decorator that creates a slash command.

    Parameters
    ----------
    name : str
        The name of the slash command.
    description : str
        The description of the command
    guilds : t.Sequence[hikari.PartialGuild | hikari.Snowflakeish] | hikari.UndefinedType
        The guilds this command should be enabled in, if left as undefined, the command is global
    is_dm_enabled : bool | hikari.UndefinedType
        If True, the command is usable in direct messages
    is_nsfw : bool | hikari.UndefinedType
        If True, the command is only usable in NSFW channels
    autodefer : bool | AutodeferMode | hikari.UndefinedType
        If True, this command will be automatically deferred if it takes longer than 2 seconds to respond
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions required to use this command, these can be overriden by guild admins
    name_localizations : dict[hikari.Locale, str] | None
        Localizations for the name of this command
    description_localizations : dict[hikari.Locale, str] | None
        Localizations for the description of this command

    Returns
    -------
    t.Callable[[t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]], SlashCommand[ClientT]]
        The decorated slash command.

    !!! note
        Parameters left as `hikari.UNDEFINED` will be inherited from the parent plugin or client.

    Examples
    --------
    ```py
    @client.include
    @arc.slash_command("hi", "Say hi!")
    async def hi_slash(
        ctx: arc.GatewayContext,
        user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```
    """

    def decorator(func: CommandCallbackT[ClientT]) -> SlashCommand[ClientT]:
        guild_ids = tuple(hikari.Snowflake(i) for i in guilds) if guilds is not hikari.UNDEFINED else hikari.UNDEFINED
        options = parse_command_signature(func)

        return SlashCommand(
            callback=func,
            options=options,
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            name=name,
            description=description,
            name_localizations=name_localizations or {},
            description_localizations=description_localizations or {},
            default_permissions=default_permissions,
            guilds=guild_ids,
            is_dm_enabled=is_dm_enabled,
            is_nsfw=is_nsfw,
        )

    return decorator


def slash_subcommand(
    name: str,
    description: str = "No description provided.",
    *,
    autodefer: bool | AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED,
    name_localizations: t.Mapping[hikari.Locale, str] | None = None,
    description_localizations: t.Mapping[hikari.Locale, str] | None = None,
) -> t.Callable[[CommandCallbackT[ClientT]], SlashSubCommand[ClientT]]:
    """A decorator that creates a slash sub command. It should be included in a slash command group.

    Parameters
    ----------
    name : str
        The name of the slash command.
    description : str
        The description of the command
    autodefer : bool | AutodeferMode | hikari.UndefinedType
        If True, this command will be automatically deferred if it takes longer than 2 seconds to respond
        If undefined, then this setting will be be inherited from the parent
    name_localizations : dict[hikari.Locale, str] | None
        Localizations for the name of this command
    description_localizations : dict[hikari.Locale, str] | None
        Localizations for the description of this command

    Returns
    -------
    t.Callable[[t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]], SlashCommand[ClientT]]
        The decorated slash command.

    !!! note
        Parameters left as `hikari.UNDEFINED` will be inherited from the parent group, plugin or client.

    Examples
    --------
    ```py
    group = client.include_slash_group("group", "A group of slash commands.")

    @group.include
    @arc.slash_subcommand(name="hi", description="Say hi!")
    async def hi_slashsub(
        ctx: arc.GatewayContext,
        user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```
    """

    def decorator(func: CommandCallbackT[ClientT]) -> SlashSubCommand[ClientT]:
        options = parse_command_signature(func)

        return SlashSubCommand(
            callback=func,
            options=options,
            name=name,
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            description=description,
            name_localizations=name_localizations or {},
            description_localizations=description_localizations or {},
        )

    return decorator


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
