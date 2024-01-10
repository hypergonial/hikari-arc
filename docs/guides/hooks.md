---
title: Hooks
description: A guide on how to use hooks in arc
---

# Hooks

**Hooks** (or checks, as known in some command handlers) are a way to execute common logic before or after a command is executed. In `arc`, any function that takes a [`Context`][arc.context.base.Context] as it's sole parameter, and either returns `None` or [`HookResult`][arc.abc.hookable.HookResult] is a valid hook.

```py
from typing import Any

import arc

# Snip

def my_hook(ctx: arc.Context[Any]) -> None:
    print(f"Command {ctx.command.name} is about to run!")
```

!!! question "Can hooks be async?"
    Hooks can either be async or sync, both variants are supported.

For a list of built-in hooks, see [here](../api_reference/utils/hooks/basic.md).

## Pre-execution VS Post-execution hooks

There are two types of hooks you can add to a command, ones that run before the command is run (pre-execution) and ones that run after (post-execution).

To register a **pre-execution** hook, simply use the [`@arc.with_hook`][arc.abc.hookable.with_hook] decorator on a command.

=== "Gateway"

    ```py hl_lines="2"
    @client.include
    @arc.with_hook(my_hook)
    @arc.slash_command("name", "description")
    async def foo(ctx: arc.GatewayContext) -> None:
        ...
    ```

=== "REST"

    ```py hl_lines="2"
    @client.include
    @arc.with_hook(my_hook)
    @arc.slash_command("name", "description")
    async def foo(ctx: arc.RESTContext) -> None:
        ...
    ```

This will run `my_hook` every time *before* the command is run.

### Aborting the command

A pre-execution hook can abort the execution of a command in one of two ways:

- raise an Exception in the hook
- Return a [`HookResult`][arc.abc.hookable.HookResult] with `abort=True`.

=== "raising an Exception"

    ```py
    def my_check(ctx: arc.Context[Any]) -> None:
        if ctx.author.id != 1234567890:
            raise Exception("Unauthorized user tried to run command!")
    ```

=== "aborting with HookResult"

    ```py
    def my_check(ctx: arc.Context[Any]) -> arc.HookResult:
        if ctx.author.id != 1234567890:
            return arc.HookResult(abort=True)
        return arc.HookResult()
    ```

The difference between these two approaches is that returning a [`HookResult`][arc.abc.hookable.HookResult] with `abort=True` will silently cancel the command from being executed, while the former will raise an exception that can then be handled (and should be handled) by an error handler.

---

To register a **post-execution** hook, use the [`@arc.with_post_hook`][arc.abc.hookable.with_post_hook] on a command.

=== "Gateway"

    ```py hl_lines="2"
    @client.include
    @arc.with_post_hook(my_hook)
    @arc.slash_command("name", "description")
    async def foo(ctx: arc.GatewayContext) -> None:
        ...
    ```

=== "REST"

    ```py hl_lines="2"
    @client.include
    @arc.with_post_hook(my_hook)
    @arc.slash_command("name", "description")
    async def foo(ctx: arc.RESTContext) -> None:
        ...
    ```

These hooks will be run after the command executes, but notably, they will **not** run if any of the pre-execution hooks abort the command before it is executed.

!!! warning
    Post-execution hooks **will** run even if the command itself raises an exception. You can think of post-hooks as the `finally` branch of a `try/except` block in this sense.

## Hooks on plugins & the client

You can also add hooks to other objects:

- Slash groups & subgroups
- [Plugins](./plugins_extensions.md)
- The client

This can be done via the [`add_hook()`][arc.abc.hookable.Hookable.add_hook] and [`add_post_hook()`][arc.abc.hookable.Hookable.add_post_hook] methods.

=== "Gateway"

    ```py
    plugin = arc.GatewayPlugin("name")
    plugin.add_hook(my_hook)
    ```

=== "REST"

    ```py
    plugin = arc.RESTPlugin("name")
    plugin.add_hook(my_hook)
    ```

In the above example, we register a pre-execution hook to run before **all commands** of this plugin.

## Hook execution order

Hooks are inherited from their parent, which means that a particular command can have hooks that affect it from:

- Itself
- It's parent group (if a slash subcommmand)
- It's plugin (if any)
- The client

The hooks are evaluated from top to bottom, in the sense that first the client hooks are run, then the plugin ones, etc... Hooks are also run in the order that they were added to a command.

=== "Gateway"

    ```py
    client = arc.GatewayClient(...)
    client.add_hook(hook_a)

    plugin = arc.GatewayPlugin("name")
    plugin.add_hook(hook_b)
    plugin.add_hook(hook_c)

    group = plugin.include_slash_group(...)
    group.add_hook(hook_d)

    @group.include
    @arc.with_hook(hook_f)
    @arc.with_hook(hook_e)
    @arc.slash_subcommand("name", "description")
    async def my_command(ctx: arc.GatewayContext) -> None:
        ...
    ```

=== "REST"

    ```py
    client = arc.RESTClient(...)
    client.add_hook(hook_a)

    plugin = arc.RESTPlugin("name")
    plugin.add_hook(hook_b)
    plugin.add_hook(hook_c)

    group = plugin.include_slash_group(...)
    group.add_hook(hook_d)

    @group.include
    @arc.with_hook(hook_f)
    @arc.with_hook(hook_e)
    @arc.slash_subcommand("name", "description")
    async def my_command(ctx: arc.RESTContext) -> None:
        ...
    ```

So using this logic, the hooks above will be evaluated in the following order:

- `hook_a` - Since client hooks are evaluated first.
- `hook_b`, `hook_c` - Plugins are next.
- `hook_d` - Groups can also have hooks!
- `hook_e`, `hook_f` - Note that decorators in Python are ordered from bottom to top!

## Limiters

Limiters (or cooldowns, as known in some libraries) are a special type of pre-execution hook that can block a command's execution for a certain period of time if it's been used too much. All limiters must implement the [`LimiterProto`][arc.abc.limiter.LimiterProto] protocol to be a valid `arc` limiter.

For a list of all built-in limiters, see [here](../api_reference/utils/hooks/limiters.md).

=== "Gateway"

    ```py hl_lines="3 13"
    @client.include
    # Limit the command to 2 uses every 10 seconds per channel.
    @arc.with_hook(arc.channel_limiter(10.0, 2))
    @arc.slash_command("ping", "Pong!")
    async def ping(ctx: arc.GatewayContext) -> None:
        await ctx.respond("Pong!")


    @ping.set_error_handler
    async def ping_error_handler(
        ctx: arc.GatewayContext, error: Exception
    ) -> None:
        if isinstance(error, arc.UnderCooldownError):
            await ctx.respond(
                "Command is on cooldown!"
                f"\nTry again in `{error.retry_after}` seconds."
            )
        else:
            raise error
    ```

=== "REST"

    ```py hl_lines="3 13"
    @client.include
    # Limit the command to 2 uses every 10 seconds per channel.
    @arc.with_hook(arc.channel_limiter(10.0, 2))
    @arc.slash_command("ping", "Pong!")
    async def ping(ctx: arc.RESTContext) -> None:
        await ctx.respond("Pong!")


    @ping.set_error_handler
    async def ping_error_handler(
        ctx: arc.RESTContext, error: Exception
    ) -> None:
        if isinstance(error, arc.UnderCooldownError):
            await ctx.respond(
                "Command is on cooldown!"
                f"\nTry again in `{error.retry_after}` seconds."
            )
        else:
            raise error
    ```

!!! warning
    You should be prepared to handle [`UnderCooldownError`][arc.errors.UnderCooldownError], it gets raised by built-in limiters when a ratelimit is exceeded. For more about error handling, see the [error handling](./error_handling.md) section.

If you need to reset the limiters for a specific context during command execution, you may use [`Context.command.reset_all_limiters()`][arc.abc.command.CallableCommandProto.reset_all_limiters].
