from __future__ import annotations

import inspect
import sys
import types
import typing as t

import hikari

from arc.abc.option import OptionParams
from arc.command.option import (
    AttachmentOption,
    AttachmentParams,
    BoolOption,
    BoolParams,
    ChannelOption,
    ChannelParams,
    FloatOption,
    FloatParams,
    IntOption,
    IntParams,
    MentionableOption,
    MentionableParams,
    RoleOption,
    RoleParams,
    StrOption,
    StrParams,
    UserOption,
    UserParams,
)

if t.TYPE_CHECKING:
    from arc.abc.option import CommandOptionBase
    from arc.context import Context
    from arc.internal.types import ClientT, EventT

# pyright: reportUnnecessaryTypeIgnoreComment=false

__all__ = ("parse_command_signature", "parse_event_signature")

# This doesn't include some special cases, for the complete resolution logic see: _get_option_type()
TYPE_TO_OPTION_MAPPING: dict[type[t.Any], type[CommandOptionBase[t.Any, t.Any, t.Any]]] = {
    bool: BoolOption,
    int: IntOption,
    str: StrOption,
    float: FloatOption,
    hikari.Role: RoleOption,
    hikari.Attachment: AttachmentOption,
    hikari.User: UserOption,
}

OPT_TO_PARAMS_MAPPING: dict[type[CommandOptionBase[t.Any, t.Any, t.Any]], type[t.Any]] = {
    BoolOption: BoolParams,
    IntOption: IntParams,
    StrOption: StrParams,
    FloatOption: FloatParams,
    UserOption: UserParams,
    ChannelOption: ChannelParams,
    MentionableOption: MentionableParams,
    RoleOption: RoleParams,
    AttachmentOption: AttachmentParams,
}

BASE_CHANNEL_TYPE_MAP: dict[type[hikari.PartialChannel], hikari.ChannelType] = {
    hikari.GuildTextChannel: hikari.ChannelType.GUILD_TEXT,
    hikari.DMChannel: hikari.ChannelType.DM,
    hikari.GuildVoiceChannel: hikari.ChannelType.GUILD_VOICE,
    hikari.GroupDMChannel: hikari.ChannelType.GROUP_DM,
    hikari.GuildCategory: hikari.ChannelType.GUILD_CATEGORY,
    hikari.GuildNewsChannel: hikari.ChannelType.GUILD_NEWS,
    hikari.GuildNewsThread: hikari.ChannelType.GUILD_NEWS_THREAD,
    hikari.GuildPublicThread: hikari.ChannelType.GUILD_PUBLIC_THREAD,
    hikari.GuildPrivateThread: hikari.ChannelType.GUILD_PRIVATE_THREAD,
    hikari.GuildStageChannel: hikari.ChannelType.GUILD_STAGE,
    hikari.GuildForumChannel: hikari.ChannelType.GUILD_FORUM,
}


def _get_channel_type(channel: type[hikari.PartialChannel]) -> set[hikari.ChannelType]:
    """Get channel types from a channel."""
    if channel in (hikari.PartialChannel, hikari.InteractionChannel):
        return set()

    types: set[hikari.ChannelType] = set()
    for k, v in BASE_CHANNEL_TYPE_MAP.items():
        if issubclass(k, channel):
            types.add(v)

    return types


def _get_all_channel_types() -> dict[type[hikari.PartialChannel], set[hikari.ChannelType]]:
    """Get all channels and their corresponding channel types."""
    mapping: dict[type[hikari.PartialChannel], set[hikari.ChannelType]] = {}

    for _, attribute in inspect.getmembers(
        hikari, lambda a: isinstance(a, type) and issubclass(a, hikari.PartialChannel)
    ):
        mapping[attribute] = _get_channel_type(attribute)

    return mapping


# Python macros when
CHANNEL_TYPES_MAPPING = _get_all_channel_types()


def _get_option_type(hint: t.Any) -> type[CommandOptionBase[t.Any, t.Any, t.Any]] | None:
    """Get the option type from a type hint."""
    if _is_mentionable_union(hint):
        return MentionableOption  # pyright: ignore reportGeneralTypeIssues

    elif _is_union(hint):
        hints = [arg for arg in t.get_args(hint) if arg is not type(None)]
        first = _get_option_type(hints[0])
        # Check if it is a uniform union recursively
        if all(_get_option_type(arg) is first for arg in hints):
            return first

    elif hint in CHANNEL_TYPES_MAPPING:
        return ChannelOption  # pyright: ignore reportGeneralTypeIssues

    else:
        return TYPE_TO_OPTION_MAPPING.get(hint)


def _is_param(meta: t.Any) -> bool:
    """Return True if the metadata is a command option parameter object."""
    return isinstance(meta, OptionParams)


def _is_union(hint: t.Any) -> bool:
    """Return True if the type hint is a typing.Union. or Python 3.10's types.UnionType."""
    return t.get_origin(hint) is t.Union or t.get_origin(hint) is types.UnionType


def _is_optional_union(hint: t.Any) -> bool:
    """Return True if the type hint is a typing.Union[T, None], also known as typing.Optional[T]."""
    return t.get_origin(hint) is t.Union and len(t.get_args(hint)) == 2 and type(None) in t.get_args(hint)


def _extract_optional_type(hint: t.Any) -> type[t.Any]:
    """Convert typing.Optional[T] to T."""
    return next(arg for arg in t.get_args(hint) if arg is not type(None))


def _is_mentionable_union(hint: t.Any) -> bool:
    """Check if a type hint is a union that represents a MentionableOption.

    Parameters
    ----------
    hint : t.Any
        The type hint to check

    Returns
    -------
    bool
        Whether the type hint is a union that represents a Mentionable option
    """
    if not _is_union(hint):
        return False

    return {arg for arg in t.get_args(hint) if arg is not type(None)} == {hikari.User, hikari.Role}


def _channels_to_channel_types(channels: t.Iterable[type[hikari.PartialChannel]]) -> list[hikari.ChannelType]:
    """Turn a list of channels into a list of channel types.

    Parameters
    ----------
    channels : Iterable[hikari.PartialChannel]
        The channels to parse

    Returns
    -------
    list[hikari.ChannelType]
        The list of channel types
    """
    channel_types: set[hikari.ChannelType] = set()

    for channel in channels:
        types = CHANNEL_TYPES_MAPPING.get(channel)

        if types is None:
            raise TypeError(
                f"Unsupported channel type '{channel.__name__}'\nSupported types: {tuple(CHANNEL_TYPES_MAPPING)}"
            )

        channel_types.update(types)

    return list(channel_types)


def _parse_channel_union_type_hint(hint: t.Any) -> list[hikari.ChannelType]:
    """Turn a union of channel types into a list of channel types.

    E.g. `hikari.GuildTextChannel | hikari.DMChannel` becomes `[hikari.ChannelType.GUILD_TEXT, hikari.ChannelType.DM]`

    Parameters
    ----------
    hint : t.Any
        The type hint to parse

    Returns
    -------
    list[hikari.ChannelType]
        The list of channel types

    Raises
    ------
    TypeError
        The type hint was not a union of channel types
    """
    if not _is_union(hint):
        raise TypeError(f"Expected type hint to be 'Union', got '{hint!r}'")

    args = t.get_args(hint)

    if not all((issubclass(arg, hikari.PartialChannel)) or arg is type(None) for arg in args):
        raise TypeError(f"Union of channels is not uniform: '{hint!r}'")

    return _channels_to_channel_types(arg for arg in args if arg is not type(None))


def parse_command_signature(  # noqa: C901
    func: t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]],
) -> dict[str, CommandOptionBase[t.Any, t.Any, t.Any]]:
    """Parse a command callback function's signature and return a list of options.

    Parameters
    ----------
    func : Callable[Concatenate[Context, P], None]
        The callback function to parse

    Returns
    -------
    dict[str, Option]
        A mapping of the keyword-argument name to the parsed option

    Raises
    ------
    TypeError
        One of the type hints was not of type 'Annotated'
    TypeError
        The type hint had more than 1 metadata item
    TypeError
        Unsupported option type
    TypeError
        The params type does not match the argument type
    TypeError
        One of the union types was not supported
    """
    hints = t.get_type_hints(func, include_extras=True)
    parameters = inspect.signature(func).parameters

    options: dict[str, CommandOptionBase[t.Any, t.Any, t.Any]] = {}
    # Remove the return type
    hints.pop("return", None)

    for arg_name, hint in hints.items():
        hint: t.Any

        # Ignore non-annotated type hints
        if t.get_origin(hint) is not t.Annotated:
            # Python 3.10 has this funny behaviour where if you default a parameter to `None`,
            # it will automatically wrap it in `typing.Optional` because fuck you.
            # So we will just get the value out of the Optional if it is in one
            if tuple(sys.version_info)[:2] == (3, 10) and _is_optional_union(hint):
                hint = _extract_optional_type(hint)

                if t.get_origin(hint) is not t.Annotated:
                    continue
            else:
                continue

        if len(hint.__metadata__) != 1:
            continue

        params = hint.__metadata__[0]
        type_ = t.get_args(hint)[0]
        union = None
        is_optional = parameters[arg_name].default is not inspect.Parameter.empty

        # This may be an alluka.Injected or other type of annotation
        if not _is_param(params):
            continue

        # If it's a union, update is_optional
        if _is_union(type_):
            union = type_
            is_optional = is_optional or type(None) in t.get_args(union)

        opt_type = _get_option_type(type_)

        # If the opt_type is None, it failed to resolve
        if opt_type is None:
            raise TypeError(f"Unsupported option type: '{type_!r}'")

        # Verify the params type matches the option type
        if not isinstance(params, OPT_TO_PARAMS_MAPPING[opt_type]):
            raise TypeError(
                f"Expected params object to be of type '{OPT_TO_PARAMS_MAPPING[opt_type].__name__}', got '{type(params).__name__}'"
            )

        # If it's a union of channel types, we need to parse all channel types
        if union is not None and any(arg in CHANNEL_TYPES_MAPPING for arg in t.get_args(union)):
            channel_types = _parse_channel_union_type_hint(union)
            options[arg_name] = ChannelOption._from_params(
                name=params.name or arg_name, is_required=not is_optional, params=params, channel_types=channel_types
            )
            continue

        # If it's a single channel type, just pass the channel type
        elif type_ in CHANNEL_TYPES_MAPPING:
            options[arg_name] = ChannelOption._from_params(
                name=params.name or arg_name,
                is_required=not is_optional,
                params=params,
                channel_types=_channels_to_channel_types([type_]),
            )
            continue

        # Otherwise just build the option
        options[arg_name] = opt_type._from_params(
            name=params.name or arg_name, is_required=not is_optional, params=params
        )

    return options


def _hint_to_event(hint: t.Any) -> type[hikari.Event] | None:
    """Convert a type hint to an event type."""
    if isinstance(hint, type) and issubclass(hint, hikari.Event):
        return hint
    elif (origin := t.get_origin(hint)) and isinstance(origin, type) and issubclass(origin, hikari.Event):
        return origin


def parse_event_signature(func: t.Callable[[EventT], t.Awaitable[None]]) -> list[type[EventT]]:
    """Parse an event callback function's signature and return the event type, ignore other type hints."""
    hints = t.get_type_hints(func)

    # Remove the return type
    hints.pop("return", None)

    first = next(iter(hints.values()))

    if _is_union(first):
        events = [_hint_to_event(arg) for arg in t.get_args(first) if _hint_to_event(arg)]
        if not events:
            raise TypeError("Expected event callback to have first argument that inherits from 'hikari.Event'")
        return events  # pyright: ignore reportGeneralTypeIssues

    elif event := _hint_to_event(first):
        return [event]  # pyright: ignore reportGeneralTypeIssues

    raise TypeError(
        f"Expected event callback to have first argument that inherits from 'hikari.Event', got '{first!r}'"
    )


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
