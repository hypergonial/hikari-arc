from __future__ import annotations

import typing as t

import attr
import hikari

from ...internal.types import ClientT
from .base import OptionWithChoices, OptionWithChoicesParams

if t.TYPE_CHECKING:
    import typing_extensions as te

    from ...internal.types import AutocompleteCallbackT


class IntParams(OptionWithChoicesParams[int, ClientT]):
    """The parameters for an int option.

    Parameters
    ----------
    name : str
        The name of the option
    description : str
        The description of the option
    name_localizations : Mapping[hikari.Locale, str] | None
        The name of the option in different locales
    description_localizations : Mapping[hikari.Locale, str] | None
        The description of the option in different locales
    min : int | None
        The minimum value of the option
    max : int | None
        The maximum value of the option
    choices : t.Sequence[int | hikari.CommandChoice] | None
        The choices for the option. If provided, these will be the only valid values for the option.
    autocomplete_with : AutocompleteCallbackT[ClientT, int] | None
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
        min: int | None = None,
        max: int | None = None,
        choices: t.Sequence[int | hikari.CommandChoice] | None = None,
        autocomplete_with: AutocompleteCallbackT[ClientT, int] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            name_localizations=name_localizations,
            description_localizations=description_localizations,
            choices=choices,
            autocomplete_with=autocomplete_with,
        )
        self._min = min
        self._max = max

    @property
    def min(self) -> int | None:
        """The minimum value of the option."""
        return self._min

    @property
    def max(self) -> int | None:
        """The maximum value of the option."""
        return self._max


@attr.define(slots=True, kw_only=True)
class IntOption(OptionWithChoices[int, ClientT, IntParams[ClientT]]):
    """A slash command option that represents an int.

    ??? hint
        To add an option of this type to your command, add an argument to your command function with the following type hint:
        ```py
        opt_name: arc.Option[int, IntParams(...)]
        ```
    """

    min: int | None = None
    """The minimum value of the option."""
    max: int | None = None
    """The maximum value of the option."""

    @property
    def option_type(self) -> hikari.OptionType:
        return hikari.OptionType.INTEGER

    @classmethod
    def _from_params(cls, *, name: str, is_required: bool, params: IntParams[ClientT], **kwargs: t.Any) -> te.Self:
        return cls(
            name=name,
            description=params.description,
            is_required=is_required,
            min=params.min,
            max=params.max,
            choices=params.choices,
            autocomplete_with=params.autocomplete_with,
            name_localizations=params.name_localizations,
            description_localizations=params.description_localizations,
        )

    def _to_dict(self) -> dict[str, t.Any]:
        return {**super()._to_dict(), "min_value": self.min, "max_value": self.max}


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
