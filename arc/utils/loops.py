import abc
import asyncio
import datetime
import inspect
import sys
import traceback
import typing as t

__all__ = ("IntervalLoop", "CronLoop", "interval_loop", "cron_loop")

P = t.ParamSpec("P")


class _LoopBase(abc.ABC, t.Generic[P]):
    """An abstract base class for loops.

    Parameters
    ----------
    callback : t.Callable[P, t.Awaitable[None]]
        The coroutine to run at the specified interval.

    See Also
    --------
    - [`IntervalLoop`][arc.utils.loops.IntervalLoop]
    - [`CronLoop`][arc.utils.loops.CronLoop]
    """

    __slots__ = ("_coro", "_task", "_failed", "_stop_next")

    def __init__(self, callback: t.Callable[P, t.Awaitable[None]]) -> None:
        self._coro = callback
        self._task: asyncio.Task[None] | None = None
        self._failed: int = 0
        self._stop_next: bool = False

        if not inspect.iscoroutinefunction(self._coro):
            raise TypeError("Expected a coroutine function.")

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Call the underlying coroutine."""
        await self._coro(*args, **kwargs)

    @abc.abstractmethod
    def _get_next_run(self) -> float:
        """Get the amount of time to sleep until the next run, in seconds.
        This will be called after the coroutine has finished running.

        Returns
        -------
        float
            The number of seconds to wait before running the coroutine again.
        """

    async def _loopy_loop(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Main loop logic."""
        while not self._stop_next:
            try:
                await self._coro(*args, **kwargs)
            except Exception as e:
                traceback_msg = "\n".join(traceback.format_exception(type(e), e, e.__traceback__))
                print(f"Loop encountered exception: {e}", file=sys.stderr)
                print(traceback_msg, file=sys.stderr)

                if self._failed < 3:
                    self._failed += 1
                    await asyncio.sleep(self._get_next_run())
                else:
                    raise RuntimeError(f"Loop failed repeatedly, stopping it. Exception: {e}")
            else:
                await asyncio.sleep(self._get_next_run())
        self.cancel()

    def _create_task(self, *args: P.args, **kwargs: P.kwargs) -> asyncio.Task[None]:
        """Create the task for the loop."""
        task = asyncio.create_task(self._loopy_loop(*args, **kwargs))
        task.add_done_callback(self._handle_result)
        return task

    def _handle_result(self, task: asyncio.Task[None]) -> None:
        """Handle the result of the task."""
        if task.cancelled():
            return

        try:
            task.result()
        except Exception as e:
            traceback_msg = "\n".join(traceback.format_exception(type(e), e, e.__traceback__))
            print(f"Loop encountered exception: {e}", file=sys.stderr)
            print(traceback_msg, file=sys.stderr)

    def start(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Start the loop at the specified interval.

        Parameters
        ----------
        args : P.args
            The positional arguments to pass to the coroutine every iteration.
        kwargs : P.kwargs
            The keyword arguments to pass to the coroutine every iteration.
        """
        if self._task and not self._task.done():
            raise RuntimeError("Task is already running!")

        self._task = self._create_task(*args, **kwargs)

    def cancel(self) -> None:
        """Cancel the loop.

        If you want to stop the loop gracefully, use `stop()` instead.
        """
        if not self._task:
            return

        self._task.cancel()
        self._task = None

    def stop(self) -> None:
        """Gracefully stop the loop. This will wait for the current iteration to finish."""
        if self._task and not self._task.done():
            self._stop_next = True


class IntervalLoop(_LoopBase[P]):
    """A simple interval loop that runs a coroutine at a specified interval.

    Parameters
    ----------
    callback : t.Callable[P, t.Awaitable[None]]
        The coroutine to run at the specified interval.
    seconds : float, optional
        The number of seconds to wait before running the coroutine again.
    minutes : float, optional
        The number of minutes to wait before running the coroutine again.
    hours : float, optional
        The number of hours to wait before running the coroutine again.
    days : float, optional
        The number of days to wait before running the coroutine again.

    Raises
    ------
    ValueError
        If no interval is specified.
    TypeError
        If the passed function is not a coroutine function.

    Examples
    --------
    ```py
    loop = IntervalLoop(my_coro, seconds=5)
    loop.start()
    ```

    You may also use the decorator [`@arc.utils.interval_loop`][arc.utils.loops.interval_loop] to
    create an [`IntervalLoop`][arc.utils.loops.IntervalLoop] from a coroutine function.
    """

    __slots__ = ("_sleep",)

    def __init__(
        self,
        callback: t.Callable[P, t.Awaitable[None]],
        *,
        seconds: float | None = None,
        minutes: float | None = None,
        hours: float | None = None,
        days: float | None = None,
    ) -> None:
        super().__init__(callback)
        if not seconds and not minutes and not hours and not days:
            raise ValueError("At least one of 'seconds', 'minutes', 'hours' or 'days' must be not None.")
        else:
            seconds = seconds or 0
            minutes = minutes or 0
            hours = hours or 0
            days = hours or 0

        self._sleep: float = seconds + minutes * 60 + hours * 3600 + days * 24 * 3600

    def _get_next_run(self) -> float:
        return self._sleep


class CronLoop(_LoopBase[P]):
    """A simple interval loop that runs a coroutine at a specified interval.

    !!! warning
        To use this loop, you must install arc with the `cron` extra.

        ```sh
        pip install hikari-arc[cron]
        ```

    Parameters
    ----------
    callback : t.Callable[P, t.Awaitable[None]]
        The coroutine to run at the specified interval.
    cron_format : str
        The cron format to use. See https://en.wikipedia.org/wiki/Cron for more information.

    Raises
    ------
    ImportError
        If the `croniter` package is not installed.
    croniter.CroniterBadCronError
        If the cron format is invalid.
    TypeError
        If the passed function is not a coroutine function.

    Examples
    --------
    ```py
    loop = CronLoop(my_coro, "*/5 * * * *")
    loop.start()
    ```

    You may also use the decorator [`@arc.utils.cron_loop`][arc.utils.loops.cron_loop] to
    create a [`CronLoop`][arc.utils.loops.CronLoop] from a coroutine function.
    """

    __slots__ = ("_iter",)

    def __init__(self, callback: t.Callable[P, t.Awaitable[None]], cron_format: str) -> None:
        super().__init__(callback)

        try:
            import croniter

            self._iter = croniter.croniter(cron_format, datetime.datetime.now())
        except ImportError:
            raise ImportError("Missing dependency for CronLoop: 'croniter'")

    def _get_next_run(self) -> float:
        return self._iter.get_next(float) - datetime.datetime.now().timestamp()


def interval_loop(
    *, seconds: float | None = None, minutes: float | None = None, hours: float | None = None, days: float | None = None
) -> t.Callable[[t.Callable[P, t.Awaitable[None]]], IntervalLoop[P]]:
    """A decorator to create an [`IntervalLoop`][arc.utils.loops.IntervalLoop] out of a coroutine function.

    Parameters
    ----------
    seconds : float, optional
        The number of seconds to wait before running the coroutine again.
    minutes : float, optional
        The number of minutes to wait before running the coroutine again.
    hours : float, optional
        The number of hours to wait before running the coroutine again.
    days : float, optional
        The number of days to wait before running the coroutine again.

    Returns
    -------
    t.Callable[[t.Callable[P, t.Awaitable[None]]], IntervalLoop[P]]
        The decorator.

    Raises
    ------
    ValueError
        If no interval is specified.
    TypeError
        If the decorated function is not a coroutine function.

    Examples
    --------
    ```py
    import arc

    # Run every 5 seconds.
    @arc.utils.interval_loop(seconds=5)
    async def my_loop():
        print("Hello, loop!")

    # Elsewhere...

    my_loop.start()
    ```
    """

    def decorator(coro: t.Callable[P, t.Awaitable[None]]) -> IntervalLoop[P]:
        return IntervalLoop(coro, seconds=seconds, minutes=minutes, hours=hours, days=days)

    return decorator


def cron_loop(cron_format: str) -> t.Callable[[t.Callable[P, t.Awaitable[None]]], CronLoop[P]]:
    """Decorator to create a [`CronLoop`][arc.utils.loops.CronLoop] out of a coroutine function.

    !!! warning
        To use this loop, you must install arc with the `cron` extra.

        ```sh
        pip install hikari-arc[cron]
        ```

    Parameters
    ----------
    cron_format : str
        The cron format to use. See https://en.wikipedia.org/wiki/Cron for more information.

    Returns
    -------
    Callable[[t.Callable[P, t.Awaitable[None]]], CronLoop[P]]
        The decorator.

    Raises
    ------
    ImportError
        If the `croniter` package is not installed.
    croniter.CroniterBadCronError
        If the cron format is invalid.
    TypeError
        If the decorated function is not a coroutine function.

    Examples
    --------
    ```py
    import arc

    # Run every 5th minute of every hour.
    @arc.utils.cron_loop("*/5 * * * *")
    async def my_loop():
        print("Hello, world!")

    # Elsewhere...

    my_loop.start()
    ```
    """

    def decorator(coro: t.Callable[P, t.Awaitable[None]]) -> CronLoop[P]:
        return CronLoop(coro, cron_format)

    return decorator


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
