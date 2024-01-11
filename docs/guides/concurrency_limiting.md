---
title: Limiting Concurrency
description: A guide on how to limit concurrently running command instances
hide:
  - toc
---

# Concurrency Limiting

In certain cases it may be useful to ensure that only a specific amount of instances of a command are running at any given time. This can be achieved by setting a **concurrency limiter**.

=== "Gateway"

    ```py hl_lines="3 12"
    @client.include
    # Limit the command to 1 instance per channel
    @arc.with_concurrency_limit(arc.channel_concurrency(1))
    @arc.slash_command("name", "description")
    async def foo(ctx: arc.GatewayContext) -> None:
        await ctx.respond("Hello, I'm running for the next 10 seconds!")
        await asyncio.sleep(10.0)
        await ctx.edit_initial_response("I'm done!")

    @foo.set_error_handler
    async def foo_error_handler(ctx: arc.GatewayContext, error: Exception) -> None:
        if isinstance(error, arc.MaxConcurrencyReachedError):
            await ctx.respond(
                "Max concurrency reached!"
                f"\nThis command can only have `{error.max_concurrency}` instances running."
            )
        else:
            raise error
    ```

=== "REST"

    ```py hl_lines="3 12"
    @client.include
    # Limit the command to 1 instance per channel
    @arc.with_concurrency_limit(arc.channel_concurrency(1))
    @arc.slash_command("name", "description")
    async def foo(ctx: arc.RESTContext) -> None:
        await ctx.respond("Hello, I'm running for the next 10 seconds!")
        await asyncio.sleep(10.0)
        await ctx.edit_initial_response("I'm done!")

    @foo.set_error_handler
    async def foo_error_handler(ctx: arc.RESTContext, error: Exception) -> None:
        if isinstance(error, arc.MaxConcurrencyReachedError):
            await ctx.respond(
                "Max concurrency reached!"
                f"\nThis command can only have `{error.max_concurrency}` instances running."
            )
        else:
            raise error
    ```

Try invoking the above command while it is still running, in the same channel! It should fail and the exception will be caught by the [error handler](./error_handling.md).

There's also other types of concurrency limiters, these are:

- [`arc.global_concurrency()`][arc.utils.concurrency_limiter.global_concurrency] - Limit concurrent instances of a command globally
- [`arc.guild_concurrency()`][arc.utils.concurrency_limiter.guild_concurrency] - Limit concurrent instances of a command per guild
- [`arc.channel_concurrency()`][arc.utils.concurrency_limiter.channel_concurrency] - Limit concurrent instances of a command per channel
- [`arc.user_concurrency()`][arc.utils.concurrency_limiter.user_concurrency] - Limit concurrent instances of a command per user
- [`arc.member_concurrency()`][arc.utils.concurrency_limiter.member_concurrency] - Limit concurrent instances of a command per user per guild
- [`arc.custom_concurrency()`][arc.utils.concurrency_limiter.custom_concurrency] - Limit concurrent instances of a command using a custom key extraction function

Concurrency limiters can be added to commands, command groups, plugins, and even the client using either the [`@arc.with_concurrency_limit()`][arc.abc.concurrency_limiting.with_concurrency_limit] decorator (as shown above) or via the [`.set_concurrency_limiter()`][arc.abc.concurrency_limiting.HasConcurrencyLimiter.set_concurrency_limiter] method.

!!! tip
    You can also define your own concurrency limiter implementations by making them conform to the [`ConcurrencyLimiterProto`][arc.abc.concurrency_limiting.ConcurrencyLimiterProto] protocol.
