# hikari-arc

A command handler for [hikari](https://github.com/hikari-py/hikari) with a focus on type-safety and correctness.

## Installation

To install arc, run the following command:

```sh
pip install -U hikari-arc
```

To check if arc has successfully installed or not, run the following:

```sh
python3 -m arc
```

> Please note that `hikari-arc` requires a Python version of *at least* 3.10.

## Basic Usage

```py
import hikari
import arc

bot = hikari.GatewayBot("TOKEN") # or hikari.RESTBot
client = arc.GatewayClient(bot) # or arc.RESTClient

@client.include
@arc.slash_command(name="hi", description="Say hi!")
async def ping(
    ctx: arc.Context[arc.GatewayClient],
    user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
) -> None:
    await ctx.respond(f"Hey {user.mention}!")

bot.run()
```
For more examples see [examples](https://github.com/hypergonial/hikari-arc/tree/main/examples), or refer to the [documentation](https://arc.hypergonial.com).

## Issues and support

For general usage help or questions, see the [hikari discord](https://discord.gg/hikari), if you have found a bug or have a feature request, feel free to [open an issue](https://github.com/hypergonial/hikari-arc/issues/new)!

## Contributing

See [Contributing](./CONTRIBUTING.md)

## Acknowledgements

`arc` is in large part a combination of all the parts I like in other command handlers, with my own spin on it. The following projects have inspired me and aided me greatly in the design of this library:

- [`hikari-lightbulb`](https://github.com/tandemdude/hikari-lightbulb) - The library initially started as a reimagination of lightbulb, it inherits a similar project structure and terminology.
- [`Tanjun`](https://github.com/FasterSpeeding/Tanjun) - For the idea of using `typing.Annotated` and dependency injection in a command handler. `arc` also uses the same dependency injection library, [`Alluka`](https://github.com/FasterSpeeding/Alluka), under the hood.
- [`FastAPI`](https://github.com/tiangolo/fastapi) - Some design ideas and most of the documentation configuration derives from `FastAPI`.

## Links

- [**Documentation**](https://arc.hypergonial.com)
- [**Examples**](https://github.com/hypergonial/hikari-arc/tree/main/examples)
- [**License**](https://github.com/hypergonial/hikari-arc/blob/main/LICENSE)
