from __future__ import annotations

import abc
import enum
import typing as t

import attr

if t.TYPE_CHECKING:
    import hikari

    from arc.abc.command import CommandProto
    from arc.abc.option import OptionBase
    from arc.context.base import Context

__all__ = (
    "LocaleRequestType",
    "LocaleRequest",
    "LocaleResponse",
    "CommandLocaleRequest",
    "OptionLocaleRequest",
    "CustomLocaleRequest",
)


@t.final
class LocaleRequestType(enum.IntEnum):
    """The type of locale request."""

    COMMAND = 0
    """A command locale request."""

    OPTION = 1
    """An option locale request."""

    CUSTOM = 2
    """A custom locale request."""


@attr.define(slots=True)
class LocaleRequest(abc.ABC):
    """The base class for all locale requests."""

    _command: CommandProto = attr.field()
    _locale: hikari.Locale = attr.field()

    @property
    @abc.abstractmethod
    def type(self) -> LocaleRequestType:
        """The type of locale request."""

    @property
    def locale(self) -> hikari.Locale:
        """The locale that is being requested."""
        return self._locale

    @property
    def command(self) -> CommandProto:
        """The command that is requesting localization."""
        return self._command

    @property
    def qualified_name(self) -> t.Sequence[str]:
        """The qualified name of the command that is requesting localization."""
        return self._command.qualified_name


@t.final
@attr.define(slots=True)
class LocaleResponse:
    """The response to a command or option locale request."""

    name: str | None = attr.field(default=None)
    """The localized name of the command or option."""

    description: str | None = attr.field(default=None)
    """The localized description of the command or option."""


@t.final
@attr.define(slots=True)
class CommandLocaleRequest(LocaleRequest):
    """A request to localize a command."""

    _name: str = attr.field()
    _description: str | None = attr.field(default=None)

    @property
    def type(self) -> LocaleRequestType:
        """The type of locale request."""
        return LocaleRequestType.COMMAND

    @property
    def name(self) -> str:
        """The name of the command to be localized."""
        return self._name

    @property
    def description(self) -> str | None:
        """The description of the command to be localized, if any."""
        return self._description


@t.final
@attr.define(slots=True)
class OptionLocaleRequest(LocaleRequest):
    """A request to localize a command option."""

    _name: str = attr.field()
    _description: str = attr.field()
    _option: OptionBase[t.Any] = attr.field()

    @property
    def type(self) -> LocaleRequestType:
        """The type of locale request."""
        return LocaleRequestType.OPTION

    @property
    def option(self) -> OptionBase[t.Any]:
        """The option that is requesting localization."""
        return self._option

    @property
    def name(self) -> str:
        """The name of the option to be localized."""
        return self._name

    @property
    def description(self) -> str:
        """The description of the option to be localized."""
        return self._description


@t.final
@attr.define(slots=True)
class CustomLocaleRequest(LocaleRequest):
    """A custom locale request made by the user."""

    _context: Context[t.Any] = attr.field()
    _key: str = attr.field()

    @property
    def type(self) -> LocaleRequestType:
        """The type of locale request."""
        return LocaleRequestType.CUSTOM

    @property
    def context(self) -> Context[t.Any]:
        """The context that is requesting localization."""
        return self._context

    @property
    def key(self) -> str:
        """The key that is to be localized."""
        return self._key


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
