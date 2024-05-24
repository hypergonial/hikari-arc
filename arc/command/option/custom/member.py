from __future__ import annotations

import typing as t

import attr
import hikari

from arc.abc.option import ConverterOption, OptionParams, OptionType
from arc.errors import OptionConverterFailureError
from arc.internal.types import ClientT

if t.TYPE_CHECKING:
    import typing_extensions as te


__all__ = ("MemberOption", "MemberParams")


@t.final
class MemberParams(OptionParams[hikari.InteractionMember]):
    """The parameters for a member option.

    Parameters
    ----------
    description : str
        The description of the option
    name : str
        The name of the option. If not provided, the name of the parameter will be used.
    name_localizations : Mapping[hikari.Locale, str] | None
        The name of the option in different locales
    description_localizations : Mapping[hikari.Locale, str] | None
        The description of the option in different locales
    """

    __slots__ = ()


@attr.define(slots=True, kw_only=True)
class MemberOption(ConverterOption[hikari.InteractionMember, ClientT, MemberParams, hikari.User]):
    """A slash command option that represents a member.

    ??? hint
        To add an option of this type to your command, add an argument to your command function with the following type hint:
        ```py
        opt_name: arc.Option[hikari.Member, MemberParams(...)]
        ```
    """

    @property
    def option_type(self) -> OptionType:
        return OptionType.MEMBER

    def _convert_value(self, value: hikari.User) -> hikari.InteractionMember:
        if isinstance(value, hikari.InteractionMember):
            return value
        raise OptionConverterFailureError(
            self, value, f"Option '{self.name}' expected an InteractionMember, got {value!r}."
        )

    @classmethod
    def _from_params(
        cls, *, name: str, arg_name: str, is_required: bool, params: MemberParams, **kwargs: t.Any
    ) -> te.Self:
        return cls(
            name=name,
            arg_name=arg_name,
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
