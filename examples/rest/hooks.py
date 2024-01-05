from typing import Any

import hikari

import arc

# Hooks are a way to execute common logic before or after a command is executed.
# Related documentation guide: https://arc.hypergonial.com/guides/hooks

bot = hikari.RESTBot("...")
client = arc.RESTClient(bot)


# Any function that takes a context as its first argument
# and returns None or HookResult is a valid hook
def my_hook(ctx: arc.Context[Any]) -> None:
    print(f"Hook was run on {ctx.command.name}!")


# Exceptions raised in hooks will abort the command
# The error can then be handled by an error handler
def my_check(ctx: arc.Context[Any]) -> None:
    if ctx.author.id != 1234567890:
        raise Exception("Unauthorized user tried to run command!")


# You can also use the HookResult class to return a result
# Note that abort=True silently cancels the command
# as opposed to raising an exception
def my_silent_check(ctx: arc.Context[Any]) -> arc.HookResult:
    if ctx.author.id != 1234567890:
        return arc.HookResult(abort=True)
    return arc.HookResult()


# Hooks can also be run after a command is executed
def cleanup_hook(ctx: arc.Context[Any]) -> None:
    print(f"Cleanup hook was run on {ctx.command.name}!")


# Hooks can be added to the client, plugins, groups, or individual commands
client.add_hook(my_check)


@client.include
@arc.with_post_hook(cleanup_hook)  # Or with '@arc.with_post_hook' to run the hook after the command
@arc.with_hook(my_hook)  # For commands, they can be added with the '@arc.with_hook' decorator
@arc.slash_command("ping", "Pong!")
async def ping(ctx: arc.RESTContext) -> None:
    await ctx.respond("Pong!")


bot.run()
