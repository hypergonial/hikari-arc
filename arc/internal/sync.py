from __future__ import annotations

import itertools
import json
import logging
import typing as t
from collections import defaultdict
from contextlib import suppress

import hikari

from arc.errors import GlobalCommandPublishFailedError, GuildCommandPublishFailedError

if t.TYPE_CHECKING:
    from arc.abc.client import Client
    from arc.abc.command import CommandBase
    from arc.internal.types import AppT

__all__ = ("_sync_commands",)

CommandMapping: t.TypeAlias = "dict[hikari.CommandType, dict[str, CommandBase[t.Any, t.Any]]]"

logger = logging.getLogger(__name__)


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
    if isinstance(command, hikari.SlashCommand):
        return hikari.impl.SlashCommandBuilder(
            name=command.name,
            id=command.id,
            description=command.description,
            options=list(command.options) if command.options else [],
            default_member_permissions=command.default_member_permissions,
            is_dm_enabled=command.is_dm_enabled,
            is_nsfw=command.is_nsfw,
            name_localizations=command.name_localizations,
            description_localizations=command.description_localizations,
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
    arc_options: list[hikari.CommandOption] = sorted(cmd_dict.get("options", None) or [], key=lambda o: o.name)
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
        and arc_options == hk_options
        and (arc_command.default_permissions or hikari.Permissions.NONE) == hk_command.default_member_permissions
        and arc_command.name_localizations == hk_command.name_localizations
        and cmd_dict.get("description_localizations", None) == getattr(hk_command, "description_localizations", None)
    )


def _get_empty_mapping() -> CommandMapping:
    """Get an empty command mapping."""
    return {hikari.CommandType.MESSAGE: {}, hikari.CommandType.USER: {}, hikari.CommandType.SLASH: {}}


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
        client._slash_commands.values(), client._message_commands.values(), client._user_commands.values()
    ):
        guild_ids = (
            command.guilds
            or (command.plugin.default_enabled_guilds if command.plugin else None)
            or client.default_enabled_guilds
            or None
        )

        if guild_ids:
            for guild_id in guild_ids:
                mapping[guild_id][command.command_type][command.name] = command
        else:
            mapping[None][command.command_type][command.name] = command

    return mapping


def _process_localizations(
    client: Client[AppT],
    commands: dict[hikari.Snowflake | None, dict[hikari.CommandType, dict[str, CommandBase[t.Any, t.Any]]]],
) -> None:
    """Call localization providers for all commands."""
    if not client._provided_locales:
        return

    logger.info("Processing localizations...")

    # trol
    for a in commands.values():
        for b in a.values():
            for command in b.values():
                command._request_command_locale()


def _extract_error(exc: Exception, builders: t.Sequence[hikari.api.CommandBuilder]) -> str:
    """Try to figure out which commands made the bot explod and include it in the error message.

    Parameters
    ----------
    exc : Exception
        The exception to extract the error from.
    builders : t.Sequence[hikari.api.CommandBuilder]
        The builders that were used to register commands, that may have caused the error.

    Returns
    -------
    str
        The error message to display.
    """
    if isinstance(exc, hikari.BadRequestError) and exc.errors:
        errors: list[str] = []

        for key in exc.errors:
            try:
                key = int(key)
            except ValueError:
                continue

            command = builders[key] if key < len(builders) else None

            if command is None:
                continue

            errors.append(
                f"Command '{command.name}' failed to register:\n{json.dumps(exc.errors[str(key)], indent=2)}\n"
            )
        if errors:
            return "\n".join(errors)

    return str(exc)


async def _perform_command_sync(  # noqa: C901
    client: Client[AppT],
    commands: CommandMapping,
    guild: hikari.SnowflakeishOr[hikari.PartialGuild] | hikari.UndefinedType = hikari.UNDEFINED,
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

    guild_id = hikari.Snowflake(guild) if guild else hikari.UNDEFINED

    if guild:
        logger.info(f"Syncing commands for guild: {guild_id}")

    unchanged, edited, created, deleted = 0, 0, 0, 0

    upstream = await client.app.rest.fetch_application_commands(client.application, guild)

    built: dict[hikari.CommandType, set[str]] = defaultdict(set)

    builders: list[hikari.api.CommandBuilder] = []

    for existing in upstream:
        # Ignore unsupported command types
        if existing.type not in commands:
            continue

        # Delete commands that don't exist locally
        elif existing.name not in commands[existing.type]:
            logger.debug(f"Command '{existing.name}' not found locally, will delete.")
            deleted += 1

        # If the command exists locally, but is not the same, edit it
        elif (local := commands[existing.type].get(existing.name)) and not _compare_commands(local, existing):
            builders.append(local._build(existing.id))
            logger.debug(f"Command '{local.name}' is out of date upstream, will edit.")
            edited += 1
        # Otherwise, keep it
        else:
            builders.append(_rebuild_hikari_command(existing))
            unchanged += 1

        built[existing.type].add(existing.name)

    for mapping in commands.values():
        for to_register in mapping.values():
            if to_register.name in built[to_register.command_type]:
                continue
            builders.append(to_register._build())
            logger.debug(f"Command '{to_register.name}' not found upstream, will create.")
            created += 1

    if edited or created or deleted:
        try:
            upstream = await client.app.rest.set_application_commands(client.application, builders, guild)
            logger.info(
                f"Guild: '{guild_id}'"
                if guild
                else "Global"
                f" - Published {created} new commands, "
                f"edited {edited} commands, deleted {deleted} commands, and left {unchanged} commands unchanged."
            )
        except Exception as e:
            if guild_id:
                raise GuildCommandPublishFailedError(
                    guild_id, f"Failed to register commands in guild {guild_id}.\n{_extract_error(e, builders)}"
                ) from e
            else:
                raise GlobalCommandPublishFailedError(
                    f"Failed to register global commands.\n{_extract_error(e, builders)}"
                ) from e

    else:
        logger.info(
            f"Commands are already up to date in guild '{guild}'"
            if guild
            else "Global commands are already up to date."
        )

    for existing in upstream:
        with suppress(KeyError):
            commands[existing.type][existing.name]._register_instance(existing, guild_id)


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
    _process_localizations(client, commands)

    global_commands = commands.pop(None, _get_empty_mapping())

    if commands:
        logger.info("Syncing guild commands...")

        for guild_id, command in commands.items():
            assert guild_id is not None
            await _perform_command_sync(client, command, guild_id)

    logger.info("Syncing global commands...")

    await _perform_command_sync(client, global_commands)

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
