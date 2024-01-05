import hikari

import arc

# Error handling is vital to any application, and arc provides a simple way to handle errors
# Related documentation guide: https://arc.hypergonial.com/guides/error_handling

bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)


@client.include
@arc.slash_command("name", "description")
async def error_command_func(
    ctx: arc.GatewayContext, recoverable: arc.Option[bool, arc.BoolParams("Is the error recoverable?")] = True
) -> None:
    if recoverable:
        raise RuntimeError("I'm an error!")
    else:
        raise Exception("I'm a fatal error!")


# You can add an error handler to a command, group, plugin, or the client
@error_command_func.set_error_handler
async def error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
    if isinstance(exc, RuntimeError):
        await ctx.respond("This is fine!")
        return
    # If you don't handle the error, you should re-raise it to send to the next error handler
    raise exc


# Setting the client error handler defines the global error handler
@client.set_error_handler
async def client_error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
    await ctx.respond("Oops, something went wrong!")

    # You should raise unhanded errors even in the global handler
    # so that a traceback is printed to the console by arc
    raise exc


# Errors are propagated from one error handler to the next until one handles it
# or you run out of error handlers

# Propagation order:
# Command -> Command Group -> Plugin -> Client

bot.run()
