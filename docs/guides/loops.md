---
title: Loops
description: A guide on creating recurring tasks via loops
hide:
  - toc
---

# Loops

**Loops** are a utility built into `arc` that allow you to repeatedly call an `async def` function with a given interval (E.g. every 30 seconds, or every hour).

To create a loop, you should decorate an async function with either [`@arc.utils.interval_loop()`][arc.utils.loops.interval_loop] or [`@arc.utils.cron_loop()`][arc.utils.loops.cron_loop], depending on your usecase.

!!! warning
    If you want to use [`@arc.utils.cron_loop()`][arc.utils.loops.cron_loop] (or [`CronLoop`][arc.utils.loops.CronLoop]), you should install `arc` with the `cron` extra:

    ```sh
    pip install hikari-arc[cron]
    ```

=== "Gateway"

    ```py
    # Create a loop out of a function
    @arc.utils.interval_loop(seconds=10.0)
    async def loopy_loop(value: int) -> None:
        print(value)

    # Somewhere else:

    @client.add_startup_hook
    async def startup(client: arc.GatewayClient) -> None:
        # Start the loop by passing all the parameters it needs
        loopy_loop.start(value=10)
    ```

=== "REST"

    ```py
    # Create a loop out of a function
    @arc.utils.interval_loop(seconds=10.0)
    async def loopy_loop(value: int) -> None:
        print(value)

    # Somewhere else:

    @client.add_startup_hook
    async def startup(client: arc.RESTClient) -> None:
        # Start the loop by passing all the parameters it needs
        loopy_loop.start(value=10)
    ```

If a decorator doesn't suit your needs, you may also use the [`IntervalLoop`][arc.utils.loops.IntervalLoop] and [`CronLoop`][arc.utils.loops.CronLoop] classes directly:

=== "Gateway"

    ```py
    async def loopy_loop(value: int) -> None:
        print(value)

    # Create a loop by passing the function in
    loop = arc.utils.IntervalLoop(loopy_loop, seconds=10.0)

    # Somewhere else:

    @client.add_startup_hook
    async def startup(client: arc.GatewayClient) -> None:
        # Start the loop by passing all the parameters it needs
        loop.start(value=10)
    ```

=== "REST"

    ```py
    async def loopy_loop(value: int) -> None:
        print(value)

    # Create a loop by passing the function in
    loop = arc.utils.IntervalLoop(loopy_loop, seconds=10.0)

    # Somewhere else:

    @client.add_startup_hook
    async def startup(client: arc.RESTClient) -> None:
        # Start the loop by passing all the parameters it needs
        loop.start(value=10)
    ```

This is identical to using the decorator from above.

To stop a loop after the next iteration, you can call `.stop()` on it, to cancel it (even mid-iteration!), call `.cancel()`.
