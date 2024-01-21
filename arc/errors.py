from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import hikari

    from arc.abc.concurrency_limiting import ConcurrencyLimiterProto
    from arc.abc.limiter import LimiterProto


class ArcError(Exception):
    """Base exception for all Arc errors."""


class AutocompleteError(ArcError):
    """An error occurred while trying to autocomplete a command."""


class CommandInvokeError(ArcError):
    """An error occurred while trying to invoke a command."""


class ExtensionError(ArcError):
    """A base exception for all extension errors."""


class ExtensionLoadError(ExtensionError):
    """An error occurred while trying to load an extension."""


class ExtensionUnloadError(ExtensionError):
    """An error occurred while trying to unload an extension."""


class InteractionResponseError(ArcError):
    """Base exception for all interaction response errors."""


class HookAbortError(ArcError):
    """Raised when a built-in hook aborts the execution of a command."""


class GuildOnlyError(HookAbortError):
    """Raised when a command is invoked outside of a guild and a
    [`guild_only`][arc.utils.hooks.guild_only] hook is present.
    """


class NotOwnerError(HookAbortError):
    """Raised when a command is invoked by a non-owner and a
    [`owner_only`][arc.utils.hooks.owner_only] hook is present.
    """


class DMOnlyError(HookAbortError):
    """Raised when a command is invoked outside of a DM and a
    [`dm_only`][arc.utils.hooks.dm_only] hook is present.
    """


class InvokerMissingPermissionsError(HookAbortError):
    """Raised when a command is invoked by a user without the
    required permissions set by a [`has_permissions`][arc.utils.hooks.has_permissions] hook.

    Attributes
    ----------
    missing_permissions : hikari.Permissions
        The permissions that the invoker is missing.
    """

    def __init__(self, missing_permissions: hikari.Permissions, *args: t.Any) -> None:
        self.missing_permissions = missing_permissions
        super().__init__(*args)


class BotMissingPermissionsError(HookAbortError):
    """Raised when a command is invoked and the bot is missing the
    required permissions set by a [`bot_has_permissions`][arc.utils.hooks.bot_has_permissions] hook.

    Attributes
    ----------
    missing_permissions : hikari.Permissions
        The permissions that the bot is missing.
    """

    def __init__(self, missing_permissions: hikari.Permissions, *args: t.Any) -> None:
        self.missing_permissions = missing_permissions
        super().__init__(*args)


class NoResponseIssuedError(InteractionResponseError):
    """Raised when no response was issued by a command.
    Interactions must be responded to or deferred within 3 seconds to avoid this error.

    `arc` tries to automatically defer responses when possible, so this error should rarely occur, unless autodefer is disabled.
    """


class ResponseAlreadyIssuedError(InteractionResponseError):
    """Raised when a response was already issued to an interaction.
    Interactions can only be issued one initial response, every other response should be a followup.

    Note that certain actions can only be done in an initial response, such as sending modals or builders.
    """


class UnderCooldownError(ArcError):
    """Raised when a built-in ratelimiter is acquired while it is exhausted, and the
    `wait` parameter is set to `False`.

    Attributes
    ----------
    limiter : arc.abc.limiter.LimiterProto
        The limiter that was rate limited.
    retry_after : float
        The amount of time in seconds until the command is off cooldown.
    """

    def __init__(self, limiter: LimiterProto[t.Any], retry_after: float, *args: t.Any) -> None:
        self.retry_after = retry_after
        self.limiter = limiter
        super().__init__(*args)


class MaxConcurrencyReachedError(ArcError):
    """Raised when a built-in concurrency limiter is acquired while it is exhausted.

    Attributes
    ----------
    limiter : arc.abc.concurrency_limiting.ConcurrencyLimiterProto
        The limiter that was exhausted.
    max_concurrency : int
        The maximum amount of concurrent instances of the command that reached max concurrency.
    """

    def __init__(self, limiter: ConcurrencyLimiterProto[t.Any], max_concurrency: int, *args: t.Any) -> None:
        self.max_concurrency = max_concurrency
        self.limiter = limiter
        super().__init__(*args)


class CommandPublishFailedError(ArcError):
    """Raised when a set of commands could not be published to Discord."""


class GlobalCommandPublishFailedError(CommandPublishFailedError):
    """Raised when a command could not be published to Discord."""


class GuildCommandPublishFailedError(CommandPublishFailedError):
    """Raised when a set of commands could not be published to a guild.

    Attributes
    ----------
    guild_id : hikari.Snowflake
        The guild that commands could not be published to.
    """

    def __init__(self, guild_id: hikari.Snowflake, *args: t.Any) -> None:
        self.guild_id = guild_id
        super().__init__(*args)


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
