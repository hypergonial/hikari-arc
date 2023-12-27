from __future__ import annotations

import typing as t

import attr
import hikari

from ...internal.types import ClientT
from .base import OptionWithChoices, OptionWithChoicesParams

if t.TYPE_CHECKING:
    import typing_extensions as te

    from ...internal.types import AutocompleteCallbackT


class StrParams(OptionWithChoicesParams[str, ClientT]):
    """The parameters for a string option.

    Parameters
    ----------
    name : str
        The name of the option
    description : str
        The description of the option
    name_localizations : Mapping[hikari.Locale, str]
        The name of the option in different locales
    description_localizations : Mapping[hikari.Locale, str]
        The description of the option in different locales
    min_length : int | None
        The minimum length of the option
    max_length : int | None
        The maximum length of the option
    choices : t.Sequence[str | hikari.CommandChoice] | None
        The choices for the option. If provided, these will be the only valid values for the option.
    autocomplete_with : AutocompleteCallbackT[ClientT, str] | None
        The callback that is invoked when the user autocompletes the option

    !!! warning
        You cannot provide both `choices` and `autocomplete_with` at the same time.
    """

    def __init__(
        self,
        name: str | None = None,
        description: str = "No description provided.",
        *,
        name_localizations: t.Mapping[hikari.Locale, str] | None = None,
        description_localizations: t.Mapping[hikari.Locale, str] | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        choices: t.Sequence[str | hikari.CommandChoice] | None = None,
        autocomplete_with: AutocompleteCallbackT[ClientT, str] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            name_localizations=name_localizations,
            description_localizations=description_localizations,
            choices=choices,
            autocomplete_with=autocomplete_with,
        )
        self._min_length = min_length
        self._max_length = max_length

    @property
    def min_length(self) -> int | None:
        """The minimum length of the option."""
        return self._min_length

    @property
    def max_length(self) -> int | None:
        """The maximum length of the option."""
        return self._max_length


@attr.define(slots=True, kw_only=True)
class StrOption(OptionWithChoices[str, ClientT, StrParams[ClientT]]):
    """A slash command option that represents a string.

    ??? hint
        To add an option of this type to your command, add an argument to your command function with the following type hint:
        ```py
        opt_name: arc.Option[str, StrParams(...)]
        ```
    """

    min_length: int | None = None
    """The minimum length of the option."""
    max_length: int | None = None
    """The maximum length of the option."""

    @property
    def option_type(self) -> hikari.OptionType:
        return hikari.OptionType.STRING

    @classmethod
    def _from_params(cls, *, name: str, is_required: bool, params: StrParams[ClientT], **kwargs: t.Any) -> te.Self:
        return cls(
            name=name,
            description=params.description,
            is_required=is_required,
            min_length=params.min_length,
            max_length=params.max_length,
            choices=params.choices,
            autocomplete_with=params.autocomplete_with,
            name_localizations=params.name_localizations,
            description_localizations=params.description_localizations,
            **kwargs,
        )

    def _to_dict(self) -> dict[str, t.Any]:
        return {**super()._to_dict(), "min_length": self.min_length, "max_length": self.max_length}


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
