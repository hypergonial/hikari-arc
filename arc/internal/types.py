from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import hikari

    from ..client import Client, GatewayClient, RESTClient
    from ..command import OptionParams, SlashCommand, SlashGroup
    from ..context import AutocompleteData, Context


# Generics
AppT = t.TypeVar("AppT", bound="hikari.RESTAware")
ChoiceT = t.TypeVar("ChoiceT", bound="int | float | str")
ClientT = t.TypeVar("ClientT", bound="Client[t.Any]")
GatewayClientT = t.TypeVar("GatewayClientT", bound="GatewayClient")
RESTClientT = t.TypeVar("RESTClientT", bound="RESTClient")
EventT = t.TypeVar("EventT", bound="hikari.Event")
BuilderT = t.TypeVar("BuilderT", bound="hikari.api.SlashCommandBuilder | hikari.api.ContextMenuCommandBuilder")
ParamsT = t.TypeVar("ParamsT", bound="OptionParams[t.Any]")

# Type aliases
EventCallbackT: t.TypeAlias = "t.Callable[[EventT], t.Coroutine[t.Any, t.Any, None]]"
ErrorHandlerCallbackT: t.TypeAlias = "t.Callable[[Context[ClientT], Exception], t.Coroutine[t.Any, t.Any, None]]"
SlashCommandLike: t.TypeAlias = "SlashCommand[ClientT] | SlashGroup[ClientT]"
CommandCallbackT: t.TypeAlias = "t.Callable[t.Concatenate[Context[ClientT], ...], t.Awaitable[None]]"
MessageContextCallbackT: t.TypeAlias = (
    "t.Callable[t.Concatenate[Context[ClientT], hikari.Message, ...], t.Awaitable[None]]"
)
UserContextCallbackT: t.TypeAlias = "t.Callable[t.Concatenate[Context[ClientT], hikari.User, ...], t.Awaitable[None]]"
AutocompleteCallbackT: t.TypeAlias = "t.Callable[[AutocompleteData[ClientT, ChoiceT]], t.Awaitable[t.Sequence[ChoiceT]]] | t.Callable[[AutocompleteData[ClientT, ChoiceT]], t.Awaitable[t.Sequence[hikari.api.AutocompleteChoiceBuilder]]]"
ResponseBuilderT: t.TypeAlias = (
    "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder | hikari.api.InteractionModalBuilder"
)
