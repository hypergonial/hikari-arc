from __future__ import annotations

import typing as t

import attr
import hikari

from arc.abc.option import CommandOptionBase, OptionParams, OptionType
from arc.internal.types import ClientT

if t.TYPE_CHECKING:
    import typing_extensions as te

__all__ = ("MentionableOption", "MentionableParams")


@t.final
class MentionableParams(OptionParams[hikari.Role | hikari.User]):
    """The parameters for a mentionable option.
    This is an option of type `hikari.Role | hikari.User`.

    Parameters
    ----------
    description : str
        The description of the option

    Other Parameters
    ----------------
    name : str
        The name of the option. If not provided, the name of the parameter will be used.
    name_localizations : Mapping[hikari.Locale, str] | None
        The name of the option in different locales
    description_localizations : Mapping[hikari.Locale, str] | None
        The description of the option in different locales
    """

    __slots__: t.Sequence[str] = ()


@attr.define(slots=True, kw_only=True)
class MentionableOption(CommandOptionBase[hikari.Role | hikari.User, ClientT, MentionableParams]):
    """A slash command option that represents a user or role.

    ??? hint
        To add an option of this type to your command, add an argument to your command function with the following type hint:
        ```py
        opt_name: arc.Option[hikari.Role | hikari.User, MentionableParams(...)]
        ```
    """

    @property
    def option_type(self) -> OptionType:
        return OptionType.MENTIONABLE

    @classmethod
    def _from_params(cls, *, name: str, is_required: bool, params: MentionableParams, **kwargs: t.Any) -> te.Self:
        return cls(
            name=name,
            description=params.description,
            is_required=is_required,
            name_localizations=params.name_localizations,
            description_localizations=params.description_localizations,
            **kwargs,
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
