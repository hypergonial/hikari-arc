---
title: Getting Started
description: Getting started with hikari-arc
hide:
  - navigation
---


# Getting Started

## Installation

To install `arc`, run the following command in your terminal:

```sh
pip install hikari-arc
```

To make sure `arc` installed correctly, run the following command:

=== "Windows"

    ```sh
    py -m arc
    ```
=== "macOS, Linux"

    ```sh
    python3 -m arc
    ```

If successful, it should output basic information about the library.

!!! note
    Please note that `arc` requires a Python version of **at least 3.10** to function.

## Basic Usage

=== "Gateway"

    ```py
    import hikari
    import arc

    bot = hikari.GatewayBot("TOKEN")
    client = arc.GatewayClient(bot)


    @client.include
    @arc.slash_command(name="hi", description="Say hi to someone!")
    async def hi_slash(
        ctx: arc.Context[arc.GatewayClient],
        user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")

    bot.run()
    ```


=== "REST"

    ```py
    import hikari
    import arc

    bot = hikari.RESTBot("TOKEN")
    client = arc.RESTClient(bot)


    @client.include
    @arc.slash_command(name="hi", description="Say hi to someone!")
    async def hi_slash(
        ctx: arc.Context[arc.RESTClient],
        user: arc.Option[hikari.User, arc.UserParams(description="The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")

    bot.run()
    ```

## Difference between Gateway & REST

<!-- TODO Finish section -->
Soon
