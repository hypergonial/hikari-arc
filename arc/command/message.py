from __future__ import annotations

import typing as t

import attr
import hikari

from arc.abc.command import CallableCommandBase
from arc.context import AutodeferMode, Context
from arc.errors import CommandInvokeError
from arc.internal.types import ClientT, MessageCommandCallbackT, ResponseBuilderT

if t.TYPE_CHECKING:
    import asyncio

    from arc.abc import CallableCommandProto

__all__ = ("MessageCommand", "message_command")


@attr.define(slots=True, kw_only=True)
class MessageCommand(CallableCommandBase[ClientT, hikari.api.ContextMenuCommandBuilder]):
    """A context menu command that is invoked by right-clicking a message."""

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.MESSAGE

    @property
    def qualified_name(self) -> t.Sequence[str]:
        return (self.name,)

    def _get_context(
        self, interaction: hikari.CommandInteraction, command: CallableCommandProto[ClientT]
    ) -> Context[ClientT]:
        assert self.client is not None

        return Context(self.client, command, interaction)

    def _build(
        self, id: hikari.Snowflake | hikari.UndefinedType = hikari.UNDEFINED
    ) -> hikari.api.ContextMenuCommandBuilder:
        return hikari.impl.ContextMenuCommandBuilder(
            name=self.name,
            id=id,
            type=self.command_type,
            default_member_permissions=self.default_permissions,
            is_dm_enabled=self.is_dm_enabled,
            is_nsfw=self.is_nsfw,
            name_localizations=self.name_localizations,  # pyright: ignore reportGeneralTypeIssues
        )

    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> asyncio.Future[ResponseBuilderT] | None:
        if interaction.command_type is not hikari.CommandType.MESSAGE:
            raise CommandInvokeError("Cannot invoke a message command with a non-message command interaction.")

        assert interaction.resolved is not None and interaction.target_id is not None

        msg = interaction.resolved.messages[interaction.target_id]

        return await super().invoke(interaction, msg, *args, **kwargs)


def message_command(
    name: str,
    *,
    guilds: t.Sequence[hikari.PartialGuild | hikari.Snowflakeish] | hikari.UndefinedType = hikari.UNDEFINED,
    is_dm_enabled: bool | hikari.UndefinedType = hikari.UNDEFINED,
    is_nsfw: bool | hikari.UndefinedType = hikari.UNDEFINED,
    autodefer: bool | AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED,
    default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
    name_localizations: t.Mapping[hikari.Locale, str] | None = None,
) -> t.Callable[[MessageCommandCallbackT[ClientT]], MessageCommand[ClientT]]:
    """A decorator that creates a context-menu command on a message.

    !!! note
        Parameters left as `hikari.UNDEFINED` will be inherited from the parent plugin or client.

    Parameters
    ----------
    name : str
        The name of the command.
    guilds : t.Sequence[hikari.PartialGuild | hikari.Snowflakeish] | hikari.UndefinedType
        The guilds this command should be enabled in, if left as undefined, the command is global
    is_dm_enabled : bool | hikari.UndefinedType
        Whether this command is enabled in DMs.
    is_nsfw : bool | hikari.UndefinedType
        Whether this command is NSFW.
    autodefer : bool | AutodeferMode | hikari.UndefinedType
        If True, this command will be automatically deferred if it takes longer than 2 seconds to respond
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for this command.
        Keep in mind that guild administrators can change this, it should only be used to provide safe defaults.
    name_localizations : t.Mapping[hikari.Locale, str] | None
        The localizations for this command's name.

    Examples
    --------
    ```py
    @client.include
    @arc.message_command(name="Say Hi", description="Say hi!")
    async def hi_msg(
        ctx: arc.GatewayContext, message: hikari.Message
    ) -> None:
        await ctx.respond(f"Hey {message.author}!")
    ```
    """

    def decorator(callback: MessageCommandCallbackT[ClientT]) -> MessageCommand[ClientT]:
        guild_ids = tuple(hikari.Snowflake(i) for i in guilds) if guilds is not hikari.UNDEFINED else hikari.UNDEFINED

        return MessageCommand(
            callback=callback,
            name=name,
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            guilds=guild_ids,
            is_dm_enabled=is_dm_enabled,
            is_nsfw=is_nsfw,
            default_permissions=default_permissions,
            name_localizations=name_localizations or {},
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
