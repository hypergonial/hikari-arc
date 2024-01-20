from __future__ import annotations

import abc
import enum
import typing as t
from typing import Any

import attr
import hikari

from arc.internal.types import AutocompleteCallbackT, ChoiceT, ClientT, ParamsT
from arc.locale import OptionLocaleRequest

if t.TYPE_CHECKING:
    import typing_extensions as te

    from arc.abc.client import Client
    from arc.abc.command import CommandProto

__all__ = (
    "Option",
    "OptionParams",
    "OptionWithChoices",
    "OptionWithChoicesParams",
    "OptionBase",
    "CommandOptionBase",
    "OptionType",
)

T = t.TypeVar("T")

Option = t.Annotated
"""Alias for typing.Annotated.

Examples
--------
```py
arc.Option[type, arc.TypeParams(...)]
```

So for example, to create an `int` option, you would do:

```py
arc.Option[int, arc.IntParams(...)]
```
"""


class OptionType(enum.IntEnum):
    """The type of a command option.

    This is practically identical to `hikari.OptionType` at the moment.
    It may however be used in the future to define custom option types.
    """

    SUB_COMMAND = 1
    """Denotes a command option where the value will be a sub command."""

    SUB_COMMAND_GROUP = 2
    """Denotes a command option where the value will be a sub command group."""

    STRING = 3
    """Denotes a command option where the value will be a string."""

    INTEGER = 4
    """Denotes a command option where the value will be a int.

    This is range limited between -2^53 and 2^53.
    """

    BOOLEAN = 5
    """Denotes a command option where the value will be a bool."""

    USER = 6
    """Denotes a command option where the value will be resolved to a user."""

    CHANNEL = 7
    """Denotes a command option where the value will be resolved to a channel."""

    ROLE = 8
    """Denotes a command option where the value will be resolved to a role."""

    MENTIONABLE = 9
    """Denotes a command option where the value will be a snowflake ID."""

    FLOAT = 10
    """Denotes a command option where the value will be a float.

    This is range limited between -2^53 and 2^53.
    """

    ATTACHMENT = 11
    """Denotes a command option where the value will be an attachment."""

    @classmethod
    def from_hikari(cls, option_type: hikari.OptionType) -> OptionType:
        """Convert a hikari.OptionType to an OptionType."""
        return cls(option_type.value)

    def to_hikari(self) -> hikari.OptionType:
        """Convert an OptionType to a hikari.OptionType."""
        # TODO: Map custom option types to their respective hikari.OptionType
        return hikari.OptionType(self.value)

    # TODO: When adding custom convertible option types, add them with an offset of 1000 or so


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

    __slots__: t.Sequence[str] = ("_name", "_description", "_name_localizations", "_description_localizations")

    def __init__(
        self,
        description: str = "No description provided.",
        *,
        name: str | None = None,
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

    !!! warning
        You cannot provide both `choices` and `autocomplete_with` at the same time.

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
    choices : t.Sequence[ChoiceT | hikari.CommandChoice] | t.Mapping[str, ChoiceT] | None
        The choices for the option. If provided, these will be the only valid values for the option.
    autocomplete_with : AutocompleteCallbackT[ClientT, ChoiceT] | None
        The callback for autocompleting the option.
    """

    __slots__: t.Sequence[str] = ("_choices", "_autocomplete_with")

    def __init__(
        self,
        description: str = "No description provided.",
        *,
        name: str | None = None,
        name_localizations: t.Mapping[hikari.Locale, str] | None = None,
        description_localizations: t.Mapping[hikari.Locale, str] | None = None,
        choices: t.Sequence[ChoiceT | hikari.CommandChoice] | t.Mapping[str, ChoiceT] | None = None,
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
    def choices(self) -> t.Sequence[ChoiceT | hikari.CommandChoice] | t.Mapping[str, ChoiceT] | None:
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
    def option_type(self) -> OptionType:
        """The type of the option. Used to register the command."""

    def _to_dict(self) -> dict[str, t.Any]:
        """Convert the option to a dictionary of kwargs that can be passed to hikari.CommandOption."""
        return {
            "type": self.option_type.to_hikari(),
            "name": self.name,
            "description": self.description,
            "autocomplete": False,
            "name_localizations": self.name_localizations,
            "description_localizations": self.description_localizations,
        }

    def to_command_option(self) -> hikari.CommandOption:
        """Convert this option to a hikari.CommandOption."""
        return hikari.CommandOption(**self._to_dict())

    def _request_option_locale(self, client: Client[t.Any], command: CommandProto) -> None:
        """Request the option's name and description in different locales."""
        if self.name_localizations or self.description_localizations:
            return

        if not client._provided_locales or not client._option_locale_provider:
            return

        name_locales: dict[hikari.Locale, str] = {}
        desc_locales: dict[hikari.Locale, str] = {}

        for locale in client._provided_locales:
            request = OptionLocaleRequest(command, locale, self.name, self.description, self)
            resp = client._option_locale_provider(request)

            if resp.name is not None and resp.description is not None:
                name_locales[locale] = resp.name
                desc_locales[locale] = resp.description

        self.name_localizations = name_locales
        self.description_localizations = desc_locales


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

    choices: t.Sequence[ChoiceT | hikari.CommandChoice] | t.Mapping[str, ChoiceT] | None = None
    """The choices for the option."""

    autocomplete_with: AutocompleteCallbackT[ClientT, ChoiceT] | None = None
    """The callback for autocompleting the option."""

    def _choices_to_command_choices(self) -> t.Sequence[hikari.CommandChoice] | None:
        if self.choices is None:
            return None

        if isinstance(self.choices, t.Mapping):
            return [hikari.CommandChoice(name=str(name), value=value) for name, value in self.choices.items()]

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
