import hikari

import arc

# Context menus commands allow you to define commands that will appear in the right-click menu of a message or user.
# Related documentation guide: https://arc.hypergonial.com/guides/context_menu

bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)

# Context-menu commands cannot be put in groups, and do not support options.
# Note that you can only define a MAXIMUM of 5 user and 5 message commands per bot.


@client.include
@arc.user_command("Say Hi")
# The user that was right-clicked is passed as a positional argument after the context.
async def hi_user(ctx: arc.GatewayContext, user: hikari.User) -> None:
    await ctx.respond(f"Hey {user.mention}!")


@client.include
@arc.message_command("Say Hi")
# The message that was right-clicked is passed as a positional argument after the context.
async def hi_message(ctx: arc.GatewayContext, message: hikari.Message) -> None:
    await ctx.respond(f"Hey {message.author.mention}!")


# Context-menu commands don't have the same naming restrictions as slash commands,
# (e.g. you can have spaces & uppercase letters),
# but two commands still cannot have the same name within the same category.

bot.run()
