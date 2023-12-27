from __future__ import annotations

import abc
import typing as t
from typing import Any

import attr
import hikari

from ...internal.types import AutocompleteCallbackT, ChoiceT, ClientT, ParamsT

if t.TYPE_CHECKING:
    import typing_extensions as te

__all__ = ("Option", "OptionParams", "OptionWithChoices", "OptionWithChoicesParams", "OptionBase", "CommandOptionBase")

T = t.TypeVar("T")

Option = t.Annotated
"""Alias for typing.Annotated.

Usage
-----
```py
arc.Option[type, arc.TypeParams(...)]
```
"""


class OptionParams(t.Generic[T]):
    """The base class for all option parameters objects.

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
    """

    def __init__(
        self,
        name: str | None = None,
        description: str = "No description provided.",
        *,
        name_localizations: t.Mapping[hikari.Locale, str] | None = None,
        description_localizations: t.Mapping[hikari.Locale, str] | None = None,
    ) -> None:
        self._description = description
        self._name = name
        self._name_localizations = name_localizations or {}
        self._description_localizations = description_localizations or {}

    @property
    def description(self) -> str:
        """The description of the option."""
        return self._description

    @property
    def name(self) -> str | None:
        """The name of the option."""
        return self._name

    @property
    def name_localizations(self) -> t.Mapping[hikari.Locale, str]:
        """The name of the option in different locales."""
        return self._name_localizations

    @property
    def description_localizations(self) -> t.Mapping[hikari.Locale, str]:
        """The description of the option in different locales."""
        return self._description_localizations


class OptionWithChoicesParams(OptionParams[ChoiceT], t.Generic[ChoiceT, ClientT]):
    """The parameters for an option that can have choices or be autocompleted.

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
    choices : t.Sequence[ChoiceT | hikari.CommandChoice] | None
        The choices for the option. If provided, these will be the only valid values for the option.
    autocomplete_with : AutocompleteCallbackT[ClientT, ChoiceT] | None
        The callback for autocompleting the option.

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
        choices: t.Sequence[ChoiceT | hikari.CommandChoice] | None = None,
        autocomplete_with: AutocompleteCallbackT[ClientT, ChoiceT] | None = None,
    ) -> None:
        super().__init__(
            description=description,
            name=name,
            name_localizations=name_localizations,
            description_localizations=description_localizations,
        )
        self._choices = choices
        self._autocomplete_with = autocomplete_with

    @property
    def choices(self) -> t.Sequence[ChoiceT | hikari.CommandChoice] | None:
        """The choices for the option. If provided, these will be the only valid values for the option."""
        return self._choices

    @property
    def autocomplete_with(self) -> AutocompleteCallbackT[ClientT, ChoiceT] | None:
        """The callback for autocompleting the option."""
        return self._autocomplete_with


@attr.define(slots=True, kw_only=True)
class OptionBase(abc.ABC, t.Generic[T]):
    """An abstract base class for all slash options and subcommands."""

    name: str
    """The name of the option."""
    description: str
    """The description of the option."""
    name_localizations: t.Mapping[hikari.Locale, str] = attr.field(factory=dict)
    """The name of the option in different locales."""
    description_localizations: t.Mapping[hikari.Locale, str] = attr.field(factory=dict)
    """The description of the option in different locales."""

    @property
    @abc.abstractmethod
    def option_type(self) -> hikari.OptionType:
        """The type of the option. Used to register the command."""

    def _to_dict(self) -> dict[str, t.Any]:
        """Convert the option to a dictionary of kwargs that can be passed to hikari.CommandOption."""
        return {
            "type": self.option_type,
            "name": self.name,
            "description": self.description,
            "autocomplete": False,
            "name_localizations": self.name_localizations,
            "description_localizations": self.description_localizations,
        }

    def to_command_option(self) -> hikari.CommandOption:
        """Convert this option to a hikari.CommandOption."""
        return hikari.CommandOption(**self._to_dict())


@attr.define(slots=True, kw_only=True)
class CommandOptionBase(OptionBase[T], t.Generic[T, ClientT, ParamsT]):
    """An abstract base class for all slash command options. This does not include subcommands."""

    is_required: bool = True
    """Whether the option is required."""

    @classmethod
    @abc.abstractmethod
    def _from_params(cls, *, name: str, is_required: bool, params: ParamsT, **kwargs: t.Any) -> te.Self:
        """Construct a new Option instance from the given parameters object.

        Parameters
        ----------
        name : str
            The name of the option
        is_required : bool
            Whether the option is required
        params : ParamsT
            The parameters for the option
        kwargs : dict[str, Any]
            Any additional keyword arguments to pass to the constructor
        """

    def _to_dict(self) -> dict[str, Any]:
        return {**super()._to_dict(), "is_required": self.is_required}


@attr.define(slots=True, kw_only=True)
class OptionWithChoices(CommandOptionBase[ChoiceT, ClientT, ParamsT]):
    """An option that can have choices or be autocompleted."""

    choices: t.Sequence[ChoiceT | hikari.CommandChoice] | None = None
    """The choices for the option."""

    autocomplete_with: AutocompleteCallbackT[ClientT, ChoiceT] | None = None
    """The callback for autocompleting the option."""

    def _choices_to_command_choices(self) -> t.Sequence[hikari.CommandChoice] | None:
        if self.choices is None:
            return None

        return [
            hikari.CommandChoice(name=str(choice), value=choice)
            if not isinstance(choice, hikari.CommandChoice)
            else choice
            for choice in self.choices
        ]

    def _to_dict(self) -> dict[str, t.Any]:
        return {
            **super()._to_dict(),
            "choices": self._choices_to_command_choices(),
            "autocomplete": self.autocomplete_with is not None,
        }


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
