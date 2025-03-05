from .concurrency_limiter import (
    CommandConcurrencyLimiter,
    ConcurrencyLimiter,
    channel_concurrency,
    custom_concurrency,
    global_concurrency,
    guild_concurrency,
    member_concurrency,
    user_concurrency,
)
from .hooks import (
    LimiterHook,
    bot_has_permissions,
    channel_limiter,
    custom_limiter,
    dm_only,
    global_limiter,
    guild_limiter,
    guild_only,
    has_permissions,
    member_limiter,
    owner_only,
    user_limiter,
)
from .loops import CronLoop, IntervalLoop, cron_loop, interval_loop
from .ratelimiter import RateLimiter, RateLimiterExhaustedError

__all__ = (
    "CommandConcurrencyLimiter",
    "ConcurrencyLimiter",
    "CronLoop",
    "IntervalLoop",
    "LimiterHook",
    "RateLimiter",
    "RateLimiterExhaustedError",
    "bot_has_permissions",
    "channel_concurrency",
    "channel_limiter",
    "cron_loop",
    "custom_concurrency",
    "custom_limiter",
    "dm_only",
    "global_concurrency",
    "global_limiter",
    "guild_concurrency",
    "guild_limiter",
    "guild_only",
    "has_permissions",
    "interval_loop",
    "member_concurrency",
    "member_limiter",
    "owner_only",
    "user_concurrency",
    "user_limiter",
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
