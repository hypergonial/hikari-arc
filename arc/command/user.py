from __future__ import annotations

import typing as t

import attr
import hikari

from arc.abc.command import CallableCommandBase
from arc.context import AutodeferMode, Context
from arc.errors import CommandInvokeError
from arc.internal.types import ClientT, ResponseBuilderT

if t.TYPE_CHECKING:
    import asyncio

    from arc.abc.command import CallableCommandProto
    from arc.internal.types import UserCommandCallbackT

__all__ = ("UserCommand", "user_command")


@attr.define(slots=True, kw_only=True)
class UserCommand(CallableCommandBase[ClientT, hikari.api.ContextMenuCommandBuilder]):
    """A context menu command that is invoked by right-clicking a user."""

    @property
    def command_type(self) -> hikari.CommandType:
        return hikari.CommandType.USER

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
            type=self.command_type,
            id=id,
            default_member_permissions=self.default_permissions,
            context_types=self.invocation_contexts,
            integration_types=self.integration_types,
            is_nsfw=self.is_nsfw,
            name_localizations={str(key): value for key, value in self.name_localizations.items()},
        )

    async def invoke(
        self, interaction: hikari.CommandInteraction, *args: t.Any, **kwargs: t.Any
    ) -> asyncio.Future[ResponseBuilderT] | None:
        if interaction.command_type is not hikari.CommandType.USER:
            raise CommandInvokeError("Cannot invoke a user command with a non-user command interaction.")

        assert interaction.resolved is not None and interaction.target_id is not None

        user = (
            interaction.resolved.members.get(interaction.target_id) or interaction.resolved.users[interaction.target_id]
        )

        return await super().invoke(interaction, user, *args, **kwargs)


def user_command(
    name: str,
    *,
    guilds: t.Sequence[hikari.PartialGuild | hikari.Snowflakeish] | hikari.UndefinedType = hikari.UNDEFINED,
    invocation_contexts: t.Sequence[hikari.ApplicationContextType] | hikari.UndefinedType = hikari.UNDEFINED,
    integration_types: t.Sequence[hikari.ApplicationIntegrationType] | hikari.UndefinedType = hikari.UNDEFINED,
    is_nsfw: bool | hikari.UndefinedType = hikari.UNDEFINED,
    autodefer: bool | AutodeferMode | hikari.UndefinedType = hikari.UNDEFINED,
    default_permissions: hikari.Permissions | hikari.UndefinedType = hikari.UNDEFINED,
    name_localizations: t.Mapping[hikari.Locale, str] | None = None,
) -> t.Callable[[UserCommandCallbackT[ClientT]], UserCommand[ClientT]]:
    """A decorator that creates a context-menu command on a user.

    !!! note
        Parameters left as `hikari.UNDEFINED` will be inherited from the parent plugin or client.

    Parameters
    ----------
    name : str
        The name of the command.
    guilds : t.Sequence[hikari.PartialGuild | hikari.Snowflakeish] | hikari.UndefinedType
        The guilds this command should be enabled in, if left as undefined, the command is global
    integration_types : t.Sequence[hikari.ApplicationIntegrationType] | hikari.UndefinedType
        The integration types this command supports the installation of
    invocation_contexts : t.Sequence[hikari.ApplicationContextType] | hikari.UndefinedType
        The context types this command can be invoked in
    is_nsfw : bool | hikari.UndefinedType
        Whether this command is NSFW.
    autodefer : bool | AutodeferMode | hikari.UndefinedType
        If True, this command will be automatically deferred if it takes longer than 2 seconds to respond
    default_permissions : hikari.Permissions | hikari.UndefinedType
        The default permissions for this command.
        Keep in mind that guild administrators can change this, it should only be used to provide safe defaults.
    name_localizations : t.Mapping[hikari.Locale, str] | None
        The localizations for this command's name.

    Example
    --------
    ```py
    @client.include
    @arc.user_command(name="Say Hi", description="Say hi!")
    async def hi_user(ctx: arc.GatewayContext, user: hikari.User) -> None:
        await ctx.respond(f"Hey {user.mention}!")
    ```
    """

    def decorator(callback: UserCommandCallbackT[ClientT]) -> UserCommand[ClientT]:
        guild_ids = tuple(hikari.Snowflake(i) for i in guilds) if guilds is not hikari.UNDEFINED else hikari.UNDEFINED

        return UserCommand(
            callback=callback,
            name=name,
            autodefer=AutodeferMode(autodefer) if isinstance(autodefer, bool) else autodefer,
            guilds=guild_ids,
            invocation_contexts=invocation_contexts,
            integration_types=integration_types,
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
