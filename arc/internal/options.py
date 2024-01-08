from __future__ import annotations

import typing as t

import hikari

from arc.abc.option import OptionType

if t.TYPE_CHECKING:
    from arc.abc.option import CommandOptionBase
    from arc.internal.types import ClientT


OPTIONTYPE_TO_TYPE: dict[OptionType, type[t.Any]] = {
    OptionType.STRING: str,
    OptionType.INTEGER: int,
    OptionType.BOOLEAN: bool,
    OptionType.USER: hikari.PartialUser,
    OptionType.CHANNEL: hikari.PartialChannel,
    OptionType.ROLE: hikari.Role,
    OptionType.MENTIONABLE: hikari.Unique,
    OptionType.FLOAT: float,
    OptionType.ATTACHMENT: hikari.Attachment,
}
"""Used for runtime type checking in Context.get_option, not much else at the moment."""


def resolve_snowflake_value(
    value: hikari.Snowflake, opt_type: hikari.OptionType | int, resolved: hikari.ResolvedOptionData
) -> t.Any:
    """Resolve a snowflake value into a resolved option.

    Parameters
    ----------
    value : hikari.Snowflake
        The snowflake value to resolve.
    opt_type : hikari.OptionType | int
        The type of the option.
    resolved : hikari.ResolvedOptionData
        The resolved option data of the interaction.

    Returns
    -------
    Any
        The resolved snowflake value.

    Raises
    ------
    ValueError
        If the option type is not a valid option type.
    """
    match opt_type:
        case hikari.OptionType.USER:
            out = resolved.members.get(value) or resolved.users[value]
        case hikari.OptionType.ATTACHMENT:
            out = resolved.attachments[value]
        case hikari.OptionType.CHANNEL:
            out = resolved.channels[value]
        case hikari.OptionType.ROLE:
            out = resolved.roles[value]
        case hikari.OptionType.MENTIONABLE:
            out = resolved.members.get(value) or resolved.users.get(value) or resolved.roles[value]
        case _:
            raise ValueError(f"Unexpected option type '{opt_type}.'")

    return out


def resolve_options(
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
            option_kwargs[arg_name] = resolve_snowflake_value(inter_opt.value, inter_opt.type, resolved)

        elif isinstance(inter_opt.value, hikari.Snowflake):
            raise ValueError(f"Missing resolved option data for '{inter_opt.name}'.")
        else:
            option_kwargs[arg_name] = inter_opt.value

    return option_kwargs
