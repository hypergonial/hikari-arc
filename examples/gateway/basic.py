import hikari

import arc

# Paste your bot token from the developer portal here in place of '...':
bot = hikari.GatewayBot("...")

# Initialize arc with the bot:
client = arc.GatewayClient(bot)


@client.include  # Add command to client
@arc.slash_command("hi", "Say hi to someone!")  # Define command
async def hi_slash(
    # The context contains information about the command invocation
    ctx: arc.GatewayContext,
    # To add an option to a command, use the following syntax:
    user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")],
) -> None:
    await ctx.respond(f"Hey {user.mention}!")


# This must be on the last line, no code will run after this:
bot.run()
