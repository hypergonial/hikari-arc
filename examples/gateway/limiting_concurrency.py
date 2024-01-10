import asyncio

import hikari

import arc

# Related documentation guide: https://arc.hypergonial.com/guides/concurrency_limiting

bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)


@client.include
# Limit the command to 1 instance per channel
@arc.with_concurrency_limit(arc.channel_concurrency(1))
@arc.slash_command("name", "description")
async def foo(ctx: arc.GatewayContext) -> None:
    await ctx.respond("Hello, I'm running for the next 10 seconds!")
    await asyncio.sleep(10.0)
    await ctx.edit_initial_response("I'm done!")


# See the error handler example for more information
@foo.set_error_handler
async def foo_error_handler(ctx: arc.GatewayContext, error: Exception) -> None:
    # If the max concurrency is exceeded, an error will be raised
    if isinstance(error, arc.MaxConcurrencyReachedError):
        await ctx.respond(
            f"Max concurrency reached!\nThis command can only have `{error.max_concurrency}` instances running."
        )
    else:
        raise error


bot.run()
