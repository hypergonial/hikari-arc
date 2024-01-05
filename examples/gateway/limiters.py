import hikari

import arc

# Limiters are a special type of pre-execution hook that can be used to limit
# the amount of times a command can be executed in a given period. You may also know them as cooldowns.

# Related documentation guide: https://arc.hypergonial.com/guides/hooks#limiters

bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)


# For a list of all built-in limiters, see https://arc.hypergonial.com/api_reference/utils/hooks/limiters/
@client.include
@arc.with_hook(arc.channel_limiter(10.0, 2))  # Limit the command to 2 uses every 10 seconds per channel.
@arc.slash_command("ping", "Pong!")
async def ping(ctx: arc.GatewayContext) -> None:
    await ctx.respond("Pong!")


# You should be prepared to handle the `UnderCooldownError` exception, as it will be raised when the limiter is exhausted.
@ping.set_error_handler
async def ping_error_handler(ctx: arc.GatewayContext, error: Exception) -> None:
    if isinstance(error, arc.UnderCooldownError):
        await ctx.respond(f"Command is on cooldown! Try again in `{error.retry_after}` seconds.")
    else:
        raise error


bot.run()
