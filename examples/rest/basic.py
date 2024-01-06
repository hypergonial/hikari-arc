import hikari

import arc

# arc should be installed with hikari-arc[rest] for this example to work.

# Note: RESTBots also support bearer tokens, along with bot tokens.

# Paste your token from the developer portal here in place of '...':
bot = hikari.RESTBot("...")

# Initialize arc with the bot:
client = arc.RESTClient(bot)


@client.include  # Add command to client
@arc.slash_command("hi", "Say hi to someone!")  # Define command
async def hi_slash(
    # The context contains information about the command invocation
    ctx: arc.RESTContext,
    # To add an option to a command, use the following syntax:
    user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")],
) -> None:
    await ctx.respond(f"Hey {user.mention}!")


# This must be on the last line, no code will run after this:
bot.run()

# Note:
# You should set the interaction URL in the developer portal to point the URL of your server.
# You may need a domain name for this, as Discord requires SSL. Hikari starts the server on port 8080 by default.

# Tip:
# For local development, certain editors such as VS Code allow you to create a temporary URL to forward a port through:
# https://code.visualstudio.com/docs/editor/port-forwarding (Do not forget to set the port publicly accessible!)

# You can also use localhost.run:
# https://localhost.run/

# This should allow you to test your bot locally without having to deploy it to a server.
