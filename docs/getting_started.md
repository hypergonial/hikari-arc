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
    @arc.slash_command("hi", "Say hi to someone!")
    async def hi_slash(
        ctx: arc.GatewayContext,
        user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")]
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
    @arc.slash_command("hi", "Say hi to someone!")
    async def hi_slash(
        ctx: arc.RESTContext,
        user: arc.Option[hikari.User, arc.UserParams("The user to say hi to.")]
    ) -> None:
        await ctx.respond(f"Hey {user.mention}!")

    bot.run()
    ```

## Difference between Gateway & REST

<!--TODO: Link events explainer to "events" word -->

There are two main ways for a bot to connect to Discord & receive events, via either a **GatewayBot** or a **RESTBot**.

A bot connected to the [**Gateway**](https://discord.com/developers/docs/topics/gateway "Discord's fancy way of saying WebSocket") needs to maintain a constant connection to Discord's servers through a [WebSocket](https://en.wikipedia.org/wiki/WebSocket),
and in turn receives **events** that inform it about things happening on Discord in real time (messages being sent, channels being created etc...).
[**Interactions**](./guides/interactions.md) are also delivered to a bot of this type through the Gateway as events. In addition, Gateway bots typically have a [*cache*][arc.client.GatewayClientBase.cache] and can manage complex state.
This model is ideal for bots that need to do things other than just responding to slash commands, such as reading messages sent by users, or acting on other server events (e.g. a moderation bot).

A **RESTBot** however, isn't constantly connected to Discord, instead, you're expected to host a small HTTP server, and Discord will send interactions to your server
that way. RESTBots **only receive interactions** from Discord, they **do not receive events** or other types of data. They are ideal for bots that manage little to no state,
and rely only on users invoking the bot via slash commands. Setting up a RESTBot however is slightly more complicated compared to a GatewayBot, as it requires a [domain](https://en.wikipedia.org/wiki/Domain_name "A domain name, like 'www.example.com'") with [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security "Transport Layer Security") for Discord to be able to send interactions to your webserver.

!!! question "Does this mean a Gateway bot cannot use the REST API?"
    **No.** Both Gateway & REST bots have access to the HTTP REST API Discord provides (see [`Client.rest`][arc.abc.client.Client.rest]), the primary difference between the two bot types is how Discord communicates with your bot, and what information it sends to it.

If you're unsure which one to choose, we recommend getting started with a **Gateway bot**.
