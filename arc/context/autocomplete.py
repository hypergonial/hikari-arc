from __future__ import annotations

import typing as t
from functools import cached_property

import attr

from arc.internal.types import ChoiceT, ClientT

if t.TYPE_CHECKING:
    import hikari

    from arc.abc.command import CommandProto

__all__ = ("AutocompleteData",)


# Don't slot, because we want to use cached_property.
@t.final
@attr.define(slots=False, kw_only=True)
class AutocompleteData(t.Generic[ClientT, ChoiceT]):
    """The data that is provided to an autocomplete callback."""

    client: ClientT
    """The client that received the autocomplete."""

    command: CommandProto
    """The command that needs to be autocompleted."""

    interaction: hikari.AutocompleteInteraction
    """The interaction that triggered the autocomplete."""

    options: t.Sequence[hikari.AutocompleteInteractionOption]
    """The options that have been provided so far."""

    @cached_property
    def focused_option(self) -> hikari.AutocompleteInteractionOption | None:
        """The option that is currently being focused."""
        return next((o for o in self.options if o.is_focused), None)

    @cached_property
    def focused_value(self) -> ChoiceT | str | None:
        """The value that is currently being focused. This property will return `None` if there is no focused option.

        !!! warning
            This property may not parsed by the client yet, in that case it is returned as a `str`.

        ??? tip
            According to some testing, this option is always either `None` or a string, however
            the API documentation says that it can be the option type as well.
        """
        if self.focused_option is None:
            return None
        return t.cast(ChoiceT | str, self.focused_option.value)

    @property
    def guild_id(self) -> hikari.Snowflake | None:
        """The guild ID of the interaction."""
        return self.interaction.guild_id

    @property
    def channel_id(self) -> hikari.Snowflake:
        """The channel ID of the interaction."""
        return self.interaction.channel_id

    @property
    def member(self) -> hikari.Member | None:
        """The member that triggered the interaction."""
        return self.interaction.member

    @property
    def user(self) -> hikari.User:
        """The user that triggered the interaction."""
        return self.interaction.user

    def get_guild(self) -> hikari.Guild | None:
        """Get the guild that triggered the interaction."""
        return self.interaction.get_guild()

    def get_channel(self) -> hikari.TextableGuildChannel | None:
        """Get the channel that triggered the interaction."""
        return self.interaction.get_channel()


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
