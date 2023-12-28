from __future__ import annotations

import inspect
import types
import typing as t

import hikari

from ..command.option import (
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
    OptionParams,
    RoleOption,
    RoleParams,
    StrOption,
    StrParams,
    UserOption,
    UserParams,
)

if t.TYPE_CHECKING:
    from ..command.option import CommandOptionBase
    from ..context import Context
    from .types import ClientT


__all__ = ("parse_function_signature",)

TYPE_TO_OPTION_MAPPING: dict[t.Type[t.Any], t.Type[CommandOptionBase[t.Any, t.Any, t.Any]]] = {
    bool: BoolOption,
    int: IntOption,
    str: StrOption,
    float: FloatOption,
    hikari.User | hikari.Role: MentionableOption,
    t.Union[hikari.User, hikari.Role]: MentionableOption,
    hikari.Attachment: AttachmentOption,
    hikari.User: UserOption,
    hikari.GuildTextChannel: ChannelOption,
    hikari.GuildVoiceChannel: ChannelOption,
    hikari.GuildCategory: ChannelOption,
    hikari.GuildNewsChannel: ChannelOption,
    hikari.GuildPrivateThread: ChannelOption,
    hikari.GuildPublicThread: ChannelOption,
    hikari.GuildForumChannel: ChannelOption,
    hikari.DMChannel: ChannelOption,
    hikari.GroupDMChannel: ChannelOption,
    hikari.GuildStageChannel: ChannelOption,
    hikari.PartialChannel: ChannelOption,
    hikari.TextableChannel: ChannelOption,
    hikari.GuildChannel: ChannelOption,
    hikari.PrivateChannel: ChannelOption,
    hikari.PermissibleGuildChannel: ChannelOption,
    hikari.TextableGuildChannel: ChannelOption,
}

OPT_TO_PARAMS_MAPPING: dict[t.Type[CommandOptionBase[t.Any, t.Any, t.Any]], t.Type[t.Any]] = {
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

# This is totally not cursed in any way
CHANNEL_TYPES_MAPPING: dict[t.Type[hikari.PartialChannel], hikari.ChannelType | set[hikari.ChannelType]] = {
    hikari.GuildTextChannel: hikari.ChannelType.GUILD_TEXT,
    hikari.GuildVoiceChannel: hikari.ChannelType.GUILD_VOICE,
    hikari.GuildCategory: hikari.ChannelType.GUILD_CATEGORY,
    hikari.GuildNewsChannel: hikari.ChannelType.GUILD_NEWS,
    hikari.GuildPrivateThread: hikari.ChannelType.GUILD_PRIVATE_THREAD,
    hikari.GuildPublicThread: hikari.ChannelType.GUILD_PUBLIC_THREAD,
    hikari.GuildForumChannel: hikari.ChannelType.GUILD_FORUM,
    hikari.DMChannel: hikari.ChannelType.DM,
    hikari.GroupDMChannel: hikari.ChannelType.GROUP_DM,
    hikari.GuildStageChannel: hikari.ChannelType.GUILD_STAGE,
    hikari.GuildThreadChannel: {
        hikari.ChannelType.GUILD_PUBLIC_THREAD,
        hikari.ChannelType.GUILD_PRIVATE_THREAD,
        hikari.ChannelType.GUILD_NEWS_THREAD,
    },
    hikari.PartialChannel: {
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
        hikari.ChannelType.GUILD_CATEGORY,
        hikari.ChannelType.GUILD_NEWS,
        hikari.ChannelType.GUILD_FORUM,
        hikari.ChannelType.GUILD_NEWS_THREAD,
        hikari.ChannelType.GUILD_PUBLIC_THREAD,
        hikari.ChannelType.GUILD_PRIVATE_THREAD,
        hikari.ChannelType.DM,
        hikari.ChannelType.GROUP_DM,
        hikari.ChannelType.GUILD_STAGE,
    },
    hikari.TextableChannel: {
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
        hikari.ChannelType.GUILD_NEWS,
        hikari.ChannelType.GUILD_NEWS_THREAD,
        hikari.ChannelType.GUILD_PUBLIC_THREAD,
        hikari.ChannelType.GUILD_PRIVATE_THREAD,
        hikari.ChannelType.DM,
        hikari.ChannelType.GROUP_DM,
        hikari.ChannelType.GUILD_STAGE,
    },
    hikari.GuildChannel: {
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
        hikari.ChannelType.GUILD_CATEGORY,
        hikari.ChannelType.GUILD_NEWS,
        hikari.ChannelType.GUILD_FORUM,
        hikari.ChannelType.GUILD_NEWS_THREAD,
        hikari.ChannelType.GUILD_PUBLIC_THREAD,
        hikari.ChannelType.GUILD_PRIVATE_THREAD,
        hikari.ChannelType.GUILD_STAGE,
    },
    hikari.PrivateChannel: {hikari.ChannelType.DM, hikari.ChannelType.GROUP_DM},
    hikari.PermissibleGuildChannel: {
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
        hikari.ChannelType.GUILD_CATEGORY,
        hikari.ChannelType.GUILD_FORUM,
        hikari.ChannelType.GUILD_NEWS,
        hikari.ChannelType.GUILD_STAGE,
    },
    hikari.TextableGuildChannel: {
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
        hikari.ChannelType.GUILD_NEWS,
        hikari.ChannelType.GUILD_NEWS_THREAD,
        hikari.ChannelType.GUILD_PUBLIC_THREAD,
        hikari.ChannelType.GUILD_PRIVATE_THREAD,
        hikari.ChannelType.GUILD_STAGE,
    },
}


def _is_param(meta: t.Any) -> bool:
    return isinstance(meta, OptionParams)


def _is_union(hint: t.Any) -> bool:
    return t.get_origin(hint) is t.Union or t.get_origin(hint) is types.UnionType


def _get_supported_types() -> list[str]:
    """Get a list of supported types.
    Used in error messages.

    Returns
    -------
    list[str]
        The list of supported types
    """
    return [type_.__name__ if type(type_) is type else repr(type_) for type_ in TYPE_TO_OPTION_MAPPING]


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


def _channels_to_channel_types(channels: t.Iterable[t.Type[hikari.PartialChannel]]) -> list[hikari.ChannelType]:
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

        if isinstance(types, set):
            channel_types.update(types)
        else:
            channel_types.add(types)

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
        raise TypeError(f"Union expressions are only supported for channels, not '{hint!r}'")

    return _channels_to_channel_types(arg for arg in args if arg is not type(None))


# TODO Detect if param has a default value and also make it optional
def parse_function_signature(  # noqa: C901
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
        # Ignore non-annotated type hints
        if t.get_origin(hint) is not t.Annotated:
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

        # If it's a union, verify all types are supported
        if _is_union(type_):
            union = type_
            union_args = t.get_args(union)

            if not _is_mentionable_union(union) and not all(
                arg is type(None) or arg in TYPE_TO_OPTION_MAPPING for arg in union_args
            ):
                raise TypeError(
                    f"Unsupported option type: '{union!r}'\nSupported option types: {_get_supported_types()}"
                )
            type_ = next((arg for arg in union_args if arg in TYPE_TO_OPTION_MAPPING))
            is_optional = is_optional or type(None) in union_args

        # Verify if it's a supported type
        elif type_ not in TYPE_TO_OPTION_MAPPING:
            raise TypeError(f"Unsupported option type: '{type_!r}'\nSupported option types: {_get_supported_types()}")

        # Get the corresponding option type
        if union is not None and _is_mentionable_union(union):
            opt_type = TYPE_TO_OPTION_MAPPING[union]
        else:
            opt_type = TYPE_TO_OPTION_MAPPING[type_]

        if not isinstance(params, OPT_TO_PARAMS_MAPPING[opt_type]):
            raise TypeError(
                f"Expected params object to be of type {OPT_TO_PARAMS_MAPPING[opt_type].__name__}, got '{type(params).__name__}'"
            )

        # If it's a union of channel types, we need to parse all channel types
        if union is not None and type_ in CHANNEL_TYPES_MAPPING:
            channel_types = _parse_channel_union_type_hint(union)
            options[arg_name] = ChannelOption._from_params(
                name=params.name or arg_name, is_required=not is_optional, params=params, channel_types=channel_types
            )
            continue

        # Parse mentionable unions
        if union is not None and {arg for arg in t.get_args(union) if arg is not type(None)} == {
            hikari.User,
            hikari.Role,
        }:
            options[arg_name] = MentionableOption._from_params(
                name=params.name or arg_name, is_required=not is_optional, params=params
            )
            continue

        # If it's a single channel type, just pass the channel type
        if type_ in CHANNEL_TYPES_MAPPING:
            options[arg_name] = ChannelOption._from_params(
                name=params.name or arg_name,
                is_required=not is_optional,
                params=params,
                channel_types=_channels_to_channel_types([type_]),
            )
            continue

        # Otherwise just build the option
        options[arg_name] = TYPE_TO_OPTION_MAPPING[type_]._from_params(
            name=params.name or arg_name, is_required=not is_optional, params=params
        )

    return options


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
