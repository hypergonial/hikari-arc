from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import hikari

    from arc.abc import Client, Hookable, HookResult, OptionParams
    from arc.abc.concurrency_limiting import HasConcurrencyLimiter
    from arc.client import GatewayClientBase, RESTClientBase
    from arc.command import SlashCommand, SlashGroup
    from arc.context import AutocompleteData, Context
    from arc.locale import CommandLocaleRequest, CustomLocaleRequest, LocaleResponse, OptionLocaleRequest


# Generics
AppT = t.TypeVar("AppT", bound="hikari.RESTAware")
ChoiceT = t.TypeVar("ChoiceT", bound="int | float | str")
ClientT = t.TypeVar("ClientT", bound="Client[t.Any]")
GatewayBotT = t.TypeVar("GatewayBotT", bound="hikari.GatewayBotAware")
RESTBotT = t.TypeVar("RESTBotT", bound="hikari.RESTBotAware")
GatewayClientT = t.TypeVar("GatewayClientT", bound="GatewayClientBase[t.Any]")
RESTClientT = t.TypeVar("RESTClientT", bound="RESTClientBase[t.Any]")
EventT = t.TypeVar("EventT", bound="hikari.Event")
BuilderT = t.TypeVar("BuilderT", bound="hikari.api.SlashCommandBuilder | hikari.api.ContextMenuCommandBuilder")
ParamsT = t.TypeVar("ParamsT", bound="OptionParams[t.Any]")
HookableT = t.TypeVar("HookableT", bound="Hookable[t.Any]")
HasConcurrencyLimiterT = t.TypeVar("HasConcurrencyLimiterT", bound="HasConcurrencyLimiter[t.Any]")

# Type aliases
EventCallbackT: t.TypeAlias = "t.Callable[[EventT], t.Awaitable[None]]"
ErrorHandlerCallbackT: t.TypeAlias = "t.Callable[[Context[ClientT], Exception], t.Awaitable[None]]"
SlashCommandLike: t.TypeAlias = "SlashCommand[ClientT] | SlashGroup[ClientT]"
CommandCallbackT: t.TypeAlias = "t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]"
MessageCommandCallbackT: t.TypeAlias = "t.Callable[[Context[ClientT], hikari.Message], t.Awaitable[None]]"
UserCommandCallbackT: t.TypeAlias = "t.Callable[[Context[ClientT], hikari.User], t.Awaitable[None]]"
AutocompleteCallbackT: t.TypeAlias = "t.Callable[[AutocompleteData[ClientT, ChoiceT]], t.Awaitable[t.Sequence[ChoiceT]]] | t.Callable[[AutocompleteData[ClientT, ChoiceT]], t.Awaitable[t.Sequence[hikari.api.AutocompleteChoiceBuilder]]]"
ResponseBuilderT: t.TypeAlias = (
    "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder | hikari.api.InteractionModalBuilder"
)
HookT: t.TypeAlias = "t.Callable[[Context[ClientT]], t.Awaitable[HookResult]] | t.Callable[[Context[ClientT]], HookResult] | t.Callable[[Context[ClientT]], None] | t.Callable[[Context[ClientT]], t.Awaitable[None]]"
PostHookT: t.TypeAlias = "t.Callable[[Context[ClientT]], None] | t.Callable[[Context[ClientT]], t.Awaitable[None]]"
LifeCycleHookT: t.TypeAlias = "t.Callable[[ClientT], t.Awaitable[None]]"
CommandLocaleRequestT: t.TypeAlias = "t.Callable[[CommandLocaleRequest], LocaleResponse]"
OptionLocaleRequestT: t.TypeAlias = "t.Callable[[OptionLocaleRequest], LocaleResponse]"
CustomLocaleRequestT: t.TypeAlias = "t.Callable[[CustomLocaleRequest], str]"

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
