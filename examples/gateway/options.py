import hikari

import arc

# Options allow users to provide additional information to slash commands
# Related documentation guide: https://arc.hypergonial.com/guides/options

bot = hikari.GatewayBot("...")
client = arc.GatewayClient(bot)


@client.include
@arc.slash_command("options", "All the options!")
async def all_the_options(
    ctx: arc.GatewayContext,
    # ints and floats support min and max values
    number: arc.Option[int, arc.IntParams("A whole number.", max=10, min=0)],
    # If you set choices, those will be the only valid values for the option
    floating: arc.Option[float, arc.FloatParams("A float.", choices=[1.0, 1.5, 2.0])],
    # Text options can have a max length
    text: arc.Option[str, arc.StrParams("Some text.", max_length=50)],
    # You can also use some common Discord types as options, these will be resolved by Discord
    user: arc.Option[hikari.User, arc.UserParams("A user.")],
    # To make an option not required, set a default value for it
    boolean: arc.Option[bool, arc.BoolParams("A boolean.")] = True,
    # Channel types are resolved based on the type passed to the option
    # This option for example will only allow guild channels that can have messages sent to them
    channel: arc.Option[hikari.TextableGuildChannel | None, arc.ChannelParams("A channel.")] = None,
) -> None:
    await ctx.respond(
        f"Number: `{number}`"
        f"\nFloating: `{floating}`"
        f"\nText: `{text}`"
        f"\nUser: {user.mention}"
        f"\nBoolean: `{boolean}`"
        f"\nChannel: {channel.mention if channel else '`None`'}"
    )


# Note that this is not all possible option types, for more information, see the documentation:
# https://arc.hypergonial.com/guides/options

# Autocomplete


# Define an autocompletion callback
# This can either return a list of the option type, or a list of hikari.CommandChoice
async def provide_opts(data: arc.AutocompleteData[arc.GatewayClient, str]) -> list[str]:
    if data.focused_value and len(data.focused_value) > 20:
        return ["That", "is", "so", "long!"]
    return ["Short", "is", "better!"]


# Only 'str', 'int' and 'float' support autocompletion


@client.include
@arc.slash_command("autocomplete", "Autocomplete options!")
async def autocomplete_command(
    ctx: arc.GatewayContext,
    # Set the 'autocomplete_with' parameter to the function that will be used to autocomplete the option
    complete_me: arc.Option[str, arc.StrParams("I'll complete you!", autocomplete_with=provide_opts)],
) -> None:
    await ctx.respond(f"You wrote: `{complete_me}`")


# Note that 'choices' and 'autocomplete_with' are mutually exclusive, you can only use one of them!

# It is also worth keeping in mind that as opposed to 'choices', the user CAN input values that are not in the list
# returned by the autocompletion function. You should validate your input.

bot.run()
