from __future__ import annotations

import itertools
import logging
import typing as t
from collections import defaultdict
from contextlib import suppress

import hikari

if t.TYPE_CHECKING:
    from ..client import Client
    from ..command import CommandBase
    from .types import AppT

__all__ = ("_sync_commands",)

CommandMapping: t.TypeAlias = "dict[hikari.CommandType, dict[str, CommandBase[t.Any, t.Any]]]"

logger = logging.getLogger(__name__)

# Acknowledgement: The logic behind the following code is partially adapted from hikari-lightbulb's internal.py
# https://github.com/tandemdude/hikari-lightbulb/blob/master/lightbulb/internal.py


def _command_option_to_dict(option: hikari.CommandOption) -> dict[str, t.Any]:
    """Convert a hikari.CommandOption to a dictionary for comparison.

    Parameters
    ----------
    option : hikari.CommandOption
        The option to convert.
    """
    return {
        "type": option.type,
        "name": option.name,
        "description": option.description,
        "required": option.is_required,
        "choices": option.choices,
        "options": sorted((_command_option_to_dict(suboption) for suboption in option.options), key=lambda o: o["name"])
        if option.options is not None
        else [],
        "channel_types": sorted(option.channel_types) if option.channel_types is not None else [],
        "min_value": option.min_value,
        "max_value": option.max_value,
        "autocomplete": option.autocomplete,
        "min_length": option.min_length,
        "max_length": option.max_length,
    }


def _rebuild_hikari_command(
    command: hikari.PartialCommand,
) -> hikari.api.SlashCommandBuilder | hikari.api.ContextMenuCommandBuilder:
    """Create a builder out of a partial hikari command.

    Parameters
    ----------
    command : hikari.PartialCommand
        The command to rebuild.

    Returns
    -------
    hikari.api.SlashCommandBuilder | hikari.api.ContextMenuCommandBuilder
        The builder for the command.

    Raises
    ------
    NotImplementedError
        The command type is not supported.
    """
    if command.type is hikari.CommandType.SLASH:
        return hikari.impl.SlashCommandBuilder(
            name=command.name,
            id=command.id,
            description=getattr(command, "description", "No description provided."),
            options=getattr(command, "options", []),
            default_member_permissions=command.default_member_permissions,
            is_dm_enabled=command.is_dm_enabled,
            is_nsfw=command.is_nsfw,
            name_localizations=command.name_localizations,
            description_localizations=getattr(command, "description_localizations", {}),
        )
    elif command.type is hikari.CommandType.MESSAGE or command.type is hikari.CommandType.USER:
        return hikari.impl.ContextMenuCommandBuilder(
            name=command.name,
            id=command.id,
            type=command.type,
            default_member_permissions=command.default_member_permissions,
            is_dm_enabled=command.is_dm_enabled,
            is_nsfw=command.is_nsfw,
            name_localizations=command.name_localizations,
        )
    else:
        raise NotImplementedError(f"Command type {command.type} is not supported.")


def _compare_commands(arc_command: CommandBase[t.Any, t.Any], hk_command: hikari.PartialCommand) -> bool:
    """Compare an Arc command to a Hikari command.

    Parameters
    ----------
    arc_command : Command
        The Arc command to compare.
    hk_command : hikari.PartialCommand
        The Hikari command to compare.

    Returns
    -------
    bool
        Whether the two commands are equal.
    """
    cmd_dict = arc_command._to_dict()
    fl_options: list[hikari.CommandOption] = sorted(cmd_dict.get("options", None) or [], key=lambda o: o.name)
    hk_options: list[hikari.CommandOption] = sorted(getattr(hk_command, "options", None) or [], key=lambda o: o.name)

    return (
        arc_command.command_type == hk_command.type
        and arc_command.name == hk_command.name
        and cmd_dict.get("description") == getattr(hk_command, "description", None)
        and arc_command.is_nsfw == hk_command.is_nsfw
        and arc_command.is_dm_enabled == hk_command.is_dm_enabled
        and (
            hk_command.guild_id in arc_command.guilds
            if hk_command.guild_id is not None and arc_command.guilds is not hikari.UNDEFINED
            else True
        )
        and fl_options == hk_options
        and (arc_command.default_permissions or hikari.Permissions.NONE) == hk_command.default_member_permissions
        and arc_command.name_localizations == hk_command.name_localizations
        and cmd_dict.get("description_localizations", None) == getattr(hk_command, "description_localizations", None)
    )


def _get_all_commands(
    client: Client[AppT],
) -> dict[hikari.Snowflake | None, dict[hikari.CommandType, dict[str, CommandBase[t.Any, t.Any]]]]:
    """Get all commands that should be registered in each guild, with None corresponding to global commands.

    Parameters
    ----------
    client : Client[AppT]
        The client to get commands for.

    Returns
    -------
    dict[hikari.Snowflake | None, dict[hikari.CommandType, dict[str, CommandBase[t.Any, t.Any]]]]
        A mapping of guilds to command types to command names to commands that should be registered.
    """
    # The big daddy of all mappings
    mapping: dict[
        hikari.Snowflake | None, dict[hikari.CommandType, dict[str, CommandBase[t.Any, t.Any]]]
    ] = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # type: ignore

    for command in itertools.chain(
        client.slash_commands.values(), client.message_commands.values(), client.user_commands.values()
    ):
        if command.guilds:
            for guild_id in command.guilds:
                mapping[guild_id][command.command_type][command.name] = command
        elif command.plugin and command.plugin.default_enabled_guilds:
            for guild_id in command.plugin.default_enabled_guilds:
                mapping[guild_id][command.command_type][command.name] = command
        elif command.client.default_enabled_guilds:
            for guild_id in command.client.default_enabled_guilds:
                mapping[guild_id][command.command_type][command.name] = command
        else:
            mapping[None][command.command_type][command.name] = command

    return mapping


async def _sync_global_commands(client: Client[AppT], commands: CommandMapping) -> None:
    """Add, edit, and delete global commands to match the client's slash commands.

    Parameters
    ----------
    client : Client[AppT]
        The client to sync commands for.
    commands : CommandMapping
        The commands to sync.
    """
    assert client.application is not None

    unchanged, edited, created, deleted = 0, 0, 0, 0

    upstream = await client.app.rest.fetch_application_commands(client.application)

    published: set[str] = set()

    for existing in upstream:
        # Ignore unsupported command types
        if existing.type not in commands:
            continue

        # Delete commands that don't exist locally
        if existing.name not in commands[existing.type]:
            await existing.delete()
            deleted += 1
        # If the command exists locally, but is not the same, edit it
        elif (cmd := commands[existing.type][existing.name]) and not _compare_commands(cmd, existing):
            await cmd.publish()
            edited += 1
        # Otherwise, keep it
        else:
            commands[existing.type][existing.name]._register_instance(existing)
            unchanged += 1

        published.add(existing.name)

    for mapping in commands.values():
        for existing in mapping.values():
            if existing.name in published:
                continue

            await existing.publish()
            created += 1

    logger.debug(
        f"Global - Published {created} new commands, edited {edited} commands, deleted {deleted} commands, and left {unchanged} commands unchanged."
    )


async def _sync_commands_for_guild(
    client: Client[AppT], guild: hikari.SnowflakeishOr[hikari.PartialGuild], commands: CommandMapping
) -> None:
    """Add, edit, and delete commands in the given guild to match the client's slash commands.

    Parameters
    ----------
    client : Client[AppT]
        The client to sync commands for.
    guild : hikari.SnowflakeishOr[hikari.PartialGuild]
        The guild to sync commands for.
    commands : CommandMapping
        The commands to sync.
    """
    assert client.application is not None

    guild_id = hikari.Snowflake(guild)

    logger.info(f"Syncing commands for guild: {guild_id}")

    unchanged, edited, created, deleted = 0, 0, 0, 0

    upstream = await client.app.rest.fetch_application_commands(client.application, guild)

    built: set[str] = set()

    builders: list[hikari.api.CommandBuilder] = []

    for existing in upstream:
        # Ignore unsupported command types
        if existing.type not in commands:
            continue

        # Delete commands that don't exist locally
        elif existing.name not in commands[existing.type]:
            deleted += 1

        # If the command exists locally, but is not the same, edit it
        elif (local := commands[existing.type].get(existing.name)) and not _compare_commands(local, existing):
            builders.append(local._build())
            edited += 1
        # Otherwise, keep it
        else:
            builders.append(_rebuild_hikari_command(existing))
            unchanged += 1

        built.add(existing.name)

    for mapping in commands.values():
        for existing in mapping.values():
            if existing.name in built:
                continue
            builders.append(existing._build())
            created += 1

    created = await client.app.rest.set_application_commands(client.application, builders, guild)

    for existing in created:
        with suppress(KeyError):
            commands[existing.type][existing.name]._register_instance(existing, guild_id)

    logger.info(f"Synced commands for guild: {guild_id}")

    logger.debug(
        f"Guild: {guild_id} - Published {created} new commands, edited {edited} commands, deleted {deleted} commands, and left {unchanged} commands unchanged."
    )


async def _sync_commands(client: Client[AppT]) -> None:
    """Add, edit, and delete commands to match the client's slash commands.

    Parameters
    ----------
    client : Client[AppT]
        The client to sync commands for.

    Raises
    ------
    RuntimeError
        The client's application is not set.
    """
    if client.application is None:
        raise RuntimeError("Application is not set, cannot sync commands")

    commands = _get_all_commands(client)
    global_commands = commands.pop(None, None)

    if commands:
        logger.info("Syncing guild commands...")

        for guild_id, command in commands.items():
            assert guild_id is not None
            await _sync_commands_for_guild(client, guild_id, command)
            logger.info(f"Synced commands for guild: {guild_id}")

    if global_commands:
        logger.info("Syncing global commands...")

        await _sync_global_commands(client, global_commands)

    logger.info("Command syncing complete!")


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
