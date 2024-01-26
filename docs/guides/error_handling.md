---
title: Error Handling
description: A guide on handling errors in arc
hide:
  - toc
---

# Error Handling

Errors are a natural part of code, and thus, of commands too. `arc` offers you the ability to handle errors in a nice and ergonomic manner, with automatic error propagation if an error handler fails.

## Error Handlers

To register a **local error handler** on a command, group, plugin, or the client, use the [`@set_error_handler`][arc.abc.error_handler.HasErrorHandler.set_error_handler] decorator method. A function can be used as an error handler if it takes a [`Context`][arc.context.base.Context] and an [`Exception`][Exception] as it's sole parameters, returns `None`. Error handler functions must also be async.

=== "Gateway"

    ```py hl_lines="3 7"
    @client.include
    @arc.slash_command("name", "description")
    async def error_command_func(ctx: arc.GatewayContext) -> None:
        raise RuntimeError("I'm an error!")

    # 'error_command_func' in this case is the command function name
    @error_command_func.set_error_handler
    async def error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
        if isinstance(exc, RuntimeError):
            print(f"Handled error: {exc}")
            return
        raise exc
    ```

=== "REST"

    ```py hl_lines="3 7"
    @client.include
    @arc.slash_command("name", "description")
    async def error_command_func(ctx: arc.RESTContext) -> None:
        raise RuntimeError("I'm an error!")

    # 'error_command_func' in this case is the command function name
    @error_command_func.set_error_handler
    async def error_handler(ctx: arc.RESTContext, exc: Exception) -> None:
        if isinstance(exc, RuntimeError):
            print(f"Handled error: {exc}")
            return
        raise exc
    ```

!!! warning
    Errors that the current error handler cannot handle **must** be re-raised, otherwise the error will be silently ignored. This is true of the global error handler (the one added to the client) as well, otherwise **tracebacks will not be printed** to the console.

This can also be used as a regular function if using a decorator is not feasible:

=== "Gateway"

    ```py
    @arc.loader
    async def load(client: arc.GatewayClient) -> None:
        client.set_error_handler(some_func)
    ```

=== "REST"

    ```py
    @arc.loader
    async def load(client: arc.RESTClient) -> None:
        client.set_error_handler(some_func)
    ```

## Error handler resolution order

- Command
- Command Group (if any)
- Plugin (if any)
- Client

If none of the error handlers handle an exception, it will be, by default, printed to the console with a full traceback.
