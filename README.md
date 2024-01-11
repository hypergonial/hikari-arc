# hikari-arc

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/hikari-arc)](https://pypi.org/project/hikari-arc)
[![CI](https://github.com/hypergonial/hikari-arc/actions/workflows/ci.yml/badge.svg)](https://github.com/hypergonial/hikari-arc/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
![Pyright](https://badgen.net/badge/Pyright/strict/2A6DB2)

</div>

A command handler for [hikari](https://github.com/hikari-py/hikari) with a focus on type-safety and correctness.

## Installation

To install arc, run the following command:

```sh
pip install -U hikari-arc
```

To check if arc has successfully installed or not, run the following:

```sh
python3 -m arc
# On Windows you may need to run:
py -m arc
```

> [!NOTE]
> `hikari-arc` requires a Python version of *at least* 3.10.

If you're just getting started, you may also use the [template repository](https://github.com/hypergonial/arc-template) to get started with.

## Basic Usage

```py
import hikari
import arc

bot = hikari.GatewayBot("TOKEN") # or hikari.RESTBot
client = arc.GatewayClient(bot) # or arc.RESTClient

@client.include
@arc.slash_command("hi", "Say hi!")
async def ping(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")]
) -> None:
    await ctx.respond(f"Hey {user.mention}!")

bot.run()
```

To get started with `arc`, see the [documentation](https://arc.hypergonial.com), or the [examples](https://github.com/hypergonial/hikari-arc/tree/main/examples).

## Issues and support

For general usage help or questions, see the [hikari discord](https://discord.gg/hikari), if you have found a bug or have a feature request, feel free to [open an issue](https://github.com/hypergonial/hikari-arc/issues/new/choose)!

## Contributing

See [Contributing](./CONTRIBUTING.md).

## Acknowledgements

`arc` is in large part a combination of all the parts I like in other command handlers, with my own spin on it. The following projects have inspired me and aided me greatly in the design of this library:

- [`hikari-lightbulb`](https://github.com/tandemdude/hikari-lightbulb) - The library initially started as a reimagination of lightbulb, it inherits a similar project structure and terminology.
- [`Tanjun`](https://github.com/FasterSpeeding/Tanjun) - For the idea of using `typing.Annotated` and [dependency injection](https://arc.hypergonial.com/guides/dependency_injection/) in a command handler. `arc` also uses the same dependency injection library, [`Alluka`](https://github.com/FasterSpeeding/Alluka), under the hood.
- [`hikari-crescent`](https://github.com/hikari-crescent/hikari-crescent) The design of [hooks](https://arc.hypergonial.com/guides/hooks/) is largely inspired by `crescent`.
- [`FastAPI`](https://github.com/tiangolo/fastapi) - Some design ideas and most of the [documentation](https://arc.hypergonial.com/) [configuration](https://github.com/hypergonial/hikari-arc/blob/main/mkdocs.yml) derives from `FastAPI`.

## Links

- [**Documentation**](https://arc.hypergonial.com)
- [**Examples**](https://github.com/hypergonial/hikari-arc/tree/main/examples)
- [**License**](https://github.com/hypergonial/hikari-arc/blob/main/LICENSE)
