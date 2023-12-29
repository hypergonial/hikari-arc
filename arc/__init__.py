"""A command handler for hikari.

To get started, see the following links:

GitHub:
https://github.com/hypergonial/hikari-arc
Documentation:
https://arc.hypergonial.com
"""

from alluka import Client as Injector
from alluka import Injected, inject

from .client import Client, GatewayClient, RESTClient
from .command import (
    AttachmentParams,
    BoolParams,
    CallableCommandBase,
    CallableCommandProto,
    ChannelParams,
    FloatParams,
    IntParams,
    MentionableParams,
    MessageCommand,
    Option,
    RoleParams,
    SlashCommand,
    SlashGroup,
    SlashSubCommand,
    SlashSubGroup,
    StrParams,
    UserCommand,
    UserParams,
    message_command,
    slash_command,
    slash_subcommand,
    user_command,
)
from .context import AutocompleteData, AutodeferMode, Context
from .errors import ArcError, AutocompleteError, CommandInvokeError
from .events import ArcEvent, CommandErrorEvent
from .extension import loader, unloader
from .internal.about import __author__, __author_email__, __license__, __maintainer__, __url__, __version__
from .plugin import GatewayPlugin, Plugin, RESTPlugin

__all__ = (
    "__version__",
    "__author__",
    "__author_email__",
    "__license__",
    "__url__",
    "__maintainer__",
    "AutodeferMode",
    "Injected",
    "inject",
    "Injector",
    "AutocompleteData",
    "CallableCommandProto",
    "CallableCommandBase",
    "Option",
    "Context",
    "Context",
    "BoolParams",
    "IntParams",
    "StrParams",
    "FloatParams",
    "UserParams",
    "ChannelParams",
    "RoleParams",
    "MentionableParams",
    "AttachmentParams",
    "SlashCommand",
    "SlashGroup",
    "SlashSubCommand",
    "SlashSubGroup",
    "MessageCommand",
    "UserCommand",
    "message_command",
    "user_command",
    "slash_command",
    "slash_subcommand",
    "Client",
    "GatewayClient",
    "RESTClient",
    "ArcError",
    "AutocompleteError",
    "CommandInvokeError",
    "Plugin",
    "RESTPlugin",
    "GatewayPlugin",
    "loader",
    "unloader",
    "ArcEvent",
    "CommandErrorEvent",
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
