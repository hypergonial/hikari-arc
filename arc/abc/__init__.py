from alluka.abc import Client as Injector

from .client import Client
from .command import CallableCommandBase, CallableCommandProto, CommandBase, CommandProto
from .concurrency_limiting import ConcurrencyLimiterProto, HasConcurrencyLimiter, with_concurrency_limit
from .error_handler import HasErrorHandler
from .hookable import Hookable, HookResult, with_hook, with_post_hook
from .limiter import LimiterProto
from .option import (
    CommandOptionBase,
    Option,
    OptionBase,
    OptionParams,
    OptionType,
    OptionWithChoices,
    OptionWithChoicesParams,
)
from .plugin import PluginBase

__all__ = (
    "Injector",
    "HasErrorHandler",
    "HasConcurrencyLimiter",
    "CommandBase",
    "CommandProto",
    "CallableCommandProto",
    "CallableCommandBase",
    "Option",
    "OptionBase",
    "OptionType",
    "CommandOptionBase",
    "OptionParams",
    "OptionWithChoices",
    "OptionWithChoicesParams",
    "Client",
    "PluginBase",
    "Hookable",
    "HookResult",
    "LimiterProto",
    "ConcurrencyLimiterProto",
    "with_hook",
    "with_post_hook",
    "with_concurrency_limit",
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
