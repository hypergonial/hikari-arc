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
    "guild_only",
    "owner_only",
    "dm_only",
    "has_permissions",
    "bot_has_permissions",
    "global_limiter",
    "guild_limiter",
    "user_limiter",
    "member_limiter",
    "channel_limiter",
    "custom_limiter",
    "LimiterHook",
    "RateLimiter",
    "RateLimiterExhaustedError",
    "IntervalLoop",
    "interval_loop",
    "CronLoop",
    "cron_loop",
    "CommandConcurrencyLimiter",
    "ConcurrencyLimiter",
    "global_concurrency",
    "guild_concurrency",
    "channel_concurrency",
    "user_concurrency",
    "member_concurrency",
    "custom_concurrency",
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
