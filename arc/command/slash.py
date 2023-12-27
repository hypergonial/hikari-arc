from __future__ import annotations

import asyncio
import typing as t

import attr
import hikari

from ..abc import HasErrorHandler
from ..context import AutocompleteData, Context
from ..errors import AutocompleteError, CommandInvokeError
from ..internal.sigparse import parse_function_signature
from ..internal.types import ClientT, CommandCallbackT, ResponseBuilderT, SlashCommandLike
from .base import AutodeferMode, CallableCommandBase, CommandBase
from .option import OptionBase, OptionWithChoices

if t.TYPE_CHECKING:
    from asyncio.futures import Future

    from ..plugin import Plugin
    from .base import CallableCommandProto
    from .option import CommandOptionBase

__all__ = (
    "SlashCommandLike",
    "SlashCommand",
    "SlashGroup",
    "SlashSubCommand",
    "SlashSubGroup",
    "slash_command",
    "slash_subcommand",
)


def _resolve_options(
    local_options: t.MutableMapping[str, CommandOptionBase[ClientT, t.Any, t.Any]],
    incoming_options: t.Sequence[hikari.CommandInteractionOption],
    resolved: hikari.ResolvedOptionData | None,
) -> dict[str, t.Any]:
    """Resolve the options into kwargs for the callback.

    Parameters
    ----------
    local_options : t.MutableMapping[str, Option[t.Any, t.Any]]
        The options of the locally stored command.
    incoming_options : t.Sequence[hikari.CommandInteractionOption]
        The options of the interaction.
    resolved : hikari.ResolvedOptionData
        The resolved option data of the interaction.

    Returns
    -------
    dict[str, Any]
        The resolved options as kwargs, ready to be passed to the callback.
    """
    option_kwargs: dict[str, t.Any] = {}

    for arg_name, opt in local_options.items():
        inter_opt = next((o for o in incoming_options if o.name == opt.name), None)

        if inter_opt is None:
            continue

        if isinstance(inter_opt.value, hikari.Snowflake) and resolved:
            match inter_opt.type:
                case hikari.OptionType.USER:
                    value = resolved.members.get(inter_opt.value) or resolved.users[inter_opt.value]
                case hikari.OptionType.ATTACHMENT:
                    value = resolved.attachments[inter_opt.value]
                case hikari.OptionType.CHANNEL:
                    value = resolved.channels[inter_opt.value]
                case hikari.OptionType.ROLE:
                    value = resolved.roles[inter_opt.value]
                case hikari.OptionType.MENTIONABLE:
                    value = (
                        resolved.members.get(inter_opt.value)
                        or resolved.users.get(inter_opt.value)
                        or resolved.roles[inter_opt.value]
                    )
                case _:
                    raise ValueError(f"Unexpected option type '{inter_opt.type}.'")

            option_kwargs[arg_name] = value

        elif isinstance(inter_opt.value, hikari.Snowflake):
            raise ValueError(f"Missing resolved option data for '{inter_opt.name}'.")
        else:
            option_kwargs[arg_name] = inter_opt.value

    return option_kwargs


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

    description_localizations: dict[hikari.Locale, str] = attr.field(factory=dict)
    """The localizations for this command's description."""

    options: dict[str, CommandOptionBase[t.Any, ClientT, t.Any]] = attr.field(factory=dict)
    """The options of this slash command."""

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def qualified_name(self) -> t.Sequence[str]:
        return (self.name,)

    def _get_context(
        self, interaction: hikari.CommandInteraction, command: CallableCommandProto[ClientT]
    ) -> Context[ClientT]:
        assert self.client is not None

        if interaction.command_type is not hikari.CommandType.SLASH:
            raise ValueError(f"Expected slash command, got {interaction.command_type}")

        return Context(self.client, command, interaction)

    def _to_dict(self) -> dict[str, t.Any]:
        sorted_options = sorted(self.options.values(), key=lambda option: option.is_required, reverse=True)
        return {
            **super()._to_dict(),
            "description": self.description,
            "description_localizations": self.description_localizations,
            "options": [option.to_command_option() for option in sorted_options],
        }

    def _build(self) -> hikari.api.SlashCommandBuilder:
        return hikari.impl.SlashCommandBuilder(
            name=self.name,
            description=self.description,
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
                **{**kwargs, **_resolve_options(self.options, interaction.options, interaction.resolved)},
            )
        else:
            return await super().invoke(interaction, *args, **kwargs)

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


@attr.define(slots=True, kw_only=True)
class SlashGroup(CommandBase[ClientT, hikari.api.SlashCommandBuilder]):
    """A group for slash subcommands and subgroups."""

    children: dict[str, SlashSubCommand[ClientT] | SlashSubGroup[ClientT]] = attr.field(factory=dict)
    """Subcommands and subgroups that belong to this group."""

    description: str = "No description provided."
    """The description of this slash group."""

    description_localizations: dict[hikari.Locale, str] = attr.field(factory=dict)
    """The localizations for this group's description."""

    _invoke_task: asyncio.Task[t.Any] | None = attr.field(init=False, default=None)

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def qualified_name(self) -> t.Sequence[str]:
        return (self.name,)

    def _to_dict(self) -> dict[str, t.Any]:
        return {
            **super()._to_dict(),
            "description": self.description,
            "description_localizations": self.description_localizations,
            "options": [subcmd.to_command_option() for subcmd in self.children.values()],
        }

    def _get_context(
        self, interaction: hikari.CommandInteraction, command: CallableCommandProto[ClientT]
    ) -> Context[ClientT]:
        assert self.client is not None

        if interaction.command_type is not hikari.CommandType.SLASH:
            raise ValueError(f"Expected slash command, got {interaction.command_type}")

        return Context(self.client, command, interaction)

    def _build(self) -> hikari.api.SlashCommandBuilder:
        return hikari.impl.SlashCommandBuilder(
            name=self.name,
            description=self.description,
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
        *args: t.Any,
        **kwargs: t.Any,
    ) -> asyncio.Future[ResponseBuilderT] | None:
        """Invoke a subcommand."""
        ctx = self._get_context(interaction, subcommand)

        if (autodefer := subcommand._resolve_autodefer()) and autodefer.should_autodefer:
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
            return await self._invoke_subcmd(subcmd, interaction, *args, **kwargs)

        # Resolve options and invoke if it does
        if isinstance(subcmd, SlashSubCommand):
            res = _resolve_options(subcmd.options, sub.options, interaction.resolved)
            return await self._invoke_subcmd(subcmd, interaction, *args, **{**kwargs, **res})

        # Get second-order subcommand
        subsub = next((o for o in sub.options if o.name in subcmd.children), None)

        if subsub is None:
            raise CommandInvokeError(f"Slash group got unknown subcommand: '{sub.options[0]}'.")

        subsubcmd = subcmd.children[subsub.name]

        # Invoke it if it has no options
        if subsub.options is None:
            return await self._invoke_subcmd(subsubcmd, interaction, *args, **kwargs)

        # Resolve options and invoke if it does
        res = _resolve_options(subsubcmd.options, subsub.options, interaction.resolved)
        return await self._invoke_subcmd(subsubcmd, interaction, *args, **{**kwargs, **res})

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

    def include(self, command: SlashSubCommand[ClientT]) -> SlashSubCommand[ClientT]:
        """First-order decorator to add a subcommand to this group."""
        command.parent = self
        self.children[command.name] = command
        return command

    def include_subgroup(
        self,
        name: str,
        description: str = "No description provided.",
        *,
        autodefer: AutodeferMode | bool | hikari.UndefinedType = hikari.UNDEFINED,
        name_localizations: dict[hikari.Locale, str] | None = None,
        description_localizations: dict[hikari.Locale, str] | None = None,
    ) -> SlashSubGroup[ClientT]:
        """Create a subgroup and add it to this group.

        Parameters
        ----------
        name : str
            The name of the subgroup.
        description : str, optional
            The description of the subgroup, by default "No description provided."
        autodefer : bool | AutodeferMode | hikari.UndefinedType, optional
            If True, all commands in this subgroup will automatically defer if it is taking longer than 2 seconds to respond.
            If not provided, then this setting will be inherited from the parent.
        name_localizations : dict[hikari.Locale, str] | None, optional
            Localizations for the name of the subgroup, by default None
        description_localizations : dict[hikari.Locale, str] | None, optional
            Localizations for the description of the subgroup, by default None
        """
        group: SlashSubGroup[ClientT] = SlashSubGroup(
            name=name,
            description=description,
            autodefer=AutodeferMode(autodefer) if autodefer else hikari.UNDEFINED,
            name_localizations=name_localizations or {},
            description_localizations=description_localizations or {},
            parent=self,
        )
        self.children[name] = group
        return group


@attr.define(slots=True, kw_only=True)
class SlashSubGroup(OptionBase[ClientT], HasErrorHandler[ClientT]):
    """A subgroup of a slash command group."""

    parent: SlashGroup[ClientT] | None = None
    """The parent group of this subgroup."""

    children: dict[str, SlashSubCommand[ClientT]] = attr.field(factory=dict)
    """Subcommands that belong to this subgroup."""

    autodefer: AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED
    """If True, this subcommand will automatically defer if it is taking longer than 2 seconds to respond.
    If undefined, then it will be inherited from the parent.
    """

    _plugin: Plugin[ClientT] | None = attr.field(default=None, init=False)

    @property
    def option_type(self) -> hikari.OptionType:
        return hikari.OptionType.SUB_COMMAND_GROUP

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def qualified_name(self) -> t.Sequence[str]:
        if self.parent is None:
            raise ValueError("Cannot get qualified name of subgroup without parent.")

        return (self.parent.name, self.name)

    @property
    def client(self) -> ClientT:
        """The client that includes this subgroup."""
        if self.parent is None:
            raise ValueError("Cannot get client of subgroup without parent.")

        return self.parent.client

    @property
    def plugin(self) -> Plugin[ClientT] | None:
        """The plugin that includes this subgroup."""
        return self._plugin

    def _to_dict(self) -> dict[str, t.Any]:
        return {
            **super()._to_dict(),
            "options": [subcommand.to_command_option() for subcommand in self.children.values()],
        }

    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        try:
            if self.error_handler:
                await self.error_handler(ctx, exc)
            else:
                raise exc
        except Exception as e:
            assert self.parent is not None
            await self.parent._handle_exception(ctx, e)

    def include(self, command: SlashSubCommand[ClientT]) -> SlashSubCommand[ClientT]:
        """First-order decorator to add a subcommand to this group."""
        command.parent = self
        self.children[command.name] = command
        return command


@attr.define(slots=True, kw_only=True)
class SlashSubCommand(OptionBase[ClientT], HasErrorHandler[ClientT]):
    """A subcommand of a slash command group."""

    parent: SlashGroup[ClientT] | SlashSubGroup[ClientT] | None = None
    """The parent group of this subcommand."""

    callback: CommandCallbackT[ClientT]
    """The callback that will be invoked when this subcommand is invoked."""

    options: t.MutableMapping[str, CommandOptionBase[ClientT, t.Any, t.Any]] = attr.field(factory=dict)
    """The options of this subcommand."""

    autodefer: AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED
    """If True, this subcommand will automatically defer if it is taking longer than 2 seconds to respond.
    If undefined, then it will be inherited from the parent.
    """

    _invoke_task: asyncio.Task[t.Any] | None = attr.field(default=None, init=False)

    async def _handle_exception(self, ctx: Context[ClientT], exc: Exception) -> None:
        try:
            if self.error_handler:
                await self.error_handler(ctx, exc)
            else:
                raise exc
        except Exception as e:
            assert self.parent is not None
            await self.parent._handle_exception(ctx, e)

    @property
    def qualified_name(self) -> t.Sequence[str]:
        if self.parent is None:
            raise ValueError("Cannot get qualified name of subcommand without parent.")

        if isinstance(self.parent, SlashSubGroup):
            if self.parent.parent is None:
                raise ValueError("Cannot get qualified name of subcommand without parent.")

            return (self.parent.parent.name, self.parent.name, self.name)

        return (self.parent.name, self.name)

    @property
    def root(self) -> SlashGroup[ClientT]:
        """The root group of this subcommand."""
        if self.parent is None:
            raise ValueError("Cannot get root of subcommand without parent.")

        if isinstance(self.parent, SlashSubGroup):
            if self.parent.parent is None:
                raise ValueError("Cannot get root of subcommand without parent.")

            return self.parent.parent

        return self.parent

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.SLASH

    @property
    def option_type(self) -> hikari.OptionType:
        return hikari.OptionType.SUB_COMMAND

    @property
    def client(self) -> ClientT:
        """The client that includes this subcommand."""
        return self.root.client

    @property
    def plugin(self) -> Plugin[ClientT] | None:
        """The plugin that includes this subcommand."""
        return self.root.plugin

    def _resolve_autodefer(self) -> AutodeferMode:
        """Resolve autodefer for this subcommand."""
        if self.autodefer is not hikari.UNDEFINED:
            return self.autodefer

        if self.parent is None:
            return AutodeferMode.OFF

        if isinstance(self.parent, SlashSubGroup):
            if self.parent.autodefer is not hikari.UNDEFINED:
                return self.parent.autodefer

            if self.parent.parent is None:
                return AutodeferMode.OFF

            return self.parent.parent.autodefer

        return self.parent.autodefer

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
        sorted_options = sorted(self.options.values(), key=lambda option: option.is_required, reverse=True)
        return {**super()._to_dict(), "options": [option.to_command_option() for option in sorted_options]}


def slash_command(
    name: str,
    description: str = "No description provided.",
    *,
    guilds: t.Sequence[hikari.SnowflakeishOr[hikari.PartialGuild]] | None = None,
    is_dm_enabled: bool = True,
    is_nsfw: bool = False,
    autodefer: bool | AutodeferMode = True,
    default_permissions: hikari.UndefinedOr[hikari.Permissions] = hikari.UNDEFINED,
    name_localizations: dict[hikari.Locale, str] | None = None,
    description_localizations: dict[hikari.Locale, str] | None = None,
) -> t.Callable[[t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]], SlashCommand[ClientT]]:
    """A decorator that creates a slash command.

    Parameters
    ----------
    name : str
        The name of the slash command.
    description : str, optional
        The description of the command, by default "No description provided."
    guilds : t.Sequence[hikari.SnowflakeishOr[hikari.PartialGuild]] | None, optional
        The guilds this command should be enabled in, if left as None, the command is global, by default None
    is_dm_enabled : bool, optional
        If True, the command is usable in direct messages, by default True
    is_nsfw : bool, optional
        If True, the command is only usable in NSFW channels, by default False
    autodefer : bool | AutodeferMode, optional
        If True, this command will be automatically deferred if it takes longer than 2 seconds to respond, by default True
    default_permissions : hikari.UndefinedOr[hikari.Permissions], optional
        The default permissions required to use this command, these can be overriden by guild admins, by default hikari.UNDEFINED
    name_localizations : dict[hikari.Locale, str] | None, optional
        Localizations for the name of this command, by default None
    description_localizations : dict[hikari.Locale, str] | None, optional
        Localizations for the description of this command, by default None

    Returns
    -------
    t.Callable[[t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]], SlashCommand[ClientT]]
        The decorated slash command.

    Usage
    -----
    ```py
    @client.include
    @arc.slash_command(name="hi", description="Say hi!")
    async def hi_slash(
        ctx: arc.Context[arc.GatewayClient],
        user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```
    """

    def decorator(func: t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]) -> SlashCommand[ClientT]:
        guild_ids = [hikari.Snowflake(guild) for guild in guilds] if guilds else []
        options = parse_function_signature(func)

        return SlashCommand(
            callback=func,
            options=options,
            autodefer=AutodeferMode(autodefer),
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
    name_localizations: dict[hikari.Locale, str] | None = None,
    description_localizations: dict[hikari.Locale, str] | None = None,
) -> t.Callable[[t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]], SlashSubCommand[ClientT]]:
    """A decorator that creates a slash sub command. It should be included in a slash command group.

    Parameters
    ----------
    name : str
        The name of the slash command.
    description : str, optional
        The description of the command, by default "No description provided."
    autodefer : bool | AutodeferMode | hikari.UndefinedType, optional
        If True, this command will be automatically deferred if it takes longer than 2 seconds to respond, by default True
        If undefined, then this setting will be be inherited from the parent
    name_localizations : dict[hikari.Locale, str] | None, optional
        Localizations for the name of this command, by default None
    description_localizations : dict[hikari.Locale, str] | None, optional
        Localizations for the description of this command, by default None

    Returns
    -------
    t.Callable[[t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]], SlashCommand[ClientT]]
        The decorated slash command.

    Usage
    -----
    ```py
    group = client.include_group("group", "A group of slash commands.")

    @group.include
    @arc.slash_subcommand(name="hi", description="Say hi!")
    async def hi_slashsub(
        ctx: arc.Context[arc.GatewayClient],
        user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```
    """

    def decorator(
        func: t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]],
    ) -> SlashSubCommand[ClientT]:
        options = parse_function_signature(func)

        return SlashSubCommand(
            callback=func,
            options=options,
            name=name,
            autodefer=AutodeferMode(autodefer) if autodefer else hikari.UNDEFINED,
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
