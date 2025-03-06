---
title: Hikari Fundamentals
description: A guide on hikari basics needed for arc
hide:
  - toc
---

# Hikari Fundamentals

[`hikari`](https://github.com/hikari-py/hikari) is the underlying framework `arc` uses to communicate with Discord. It handles making requests to Discord, serializing & deserializing payloads, maintaining the connection the Gateway (if applicable), and more.

In this guide, you'll learn the basics of how to use `hikari` with `arc`, make common requests to Discord's REST API and access your bot's cache.

??? question "Wait, what the hell is an API?"
    An [**API**](https://en.wikipedia.org/wiki/API), or **A**pplication **P**rogramming **I**nterface, is simply a way for two computers to talk to eachother. It defines [standard message formats](# "Like JSON or HTML"), [endpoints](# "In this case, URLs to send data to"), and the rules of communication (such as [ratelimits](# "How many requests you can make in a given interval") or errors).

    For the purposes of this documentation, that's more or less all you need to know, `hikari` handles all the low-level details for you.

    Think of it this way: if a [**UI**](# "user interface") is a way for computers to talk to you, then an **API** is a way for computers to talk to eachother.

    P.S.: [**REST**](https://en.wikipedia.org/wiki/REST) stands for **R**epresentational **S**tate **T**ransfer and is simply a way of designing an API. This isn't really important to us however.

## Using Discord's REST API

The most common use for interacting with the REST API directly is if you want to make your bot *perform an action*, such as creating a channel, kicking someone, or editing guild settings. To perform a REST API call, you need to access your client's [`rest`][arc.abc.client.Client.rest] module.

=== "Gateway"

    ```py hl_lines="7"
    @client.include
    @arc.slash_command("make_channel", "Make a new channel!")
    async def make_channel(
        ctx: arc.GatewayContext,
        name: arc.Option[str, arc.StrParams("The channel's name")]
    ) -> None:
        await client.rest.create_guild_text_channel(ctx.guild_id, name)
        await ctx.respond("Channel created!")
    ```

=== "REST"

    ```py hl_lines="7"
    @client.include
    @arc.slash_command("make_channel", "Make a new channel!")
    async def make_channel(
        ctx: arc.RESTContext,
        name: arc.Option[str, arc.StrParams("The channel's name")]
    ) -> None:
        await client.rest.create_guild_text_channel(ctx.guild_id, name)
        await ctx.respond("Channel created!")
    ```

In this snippet, we use [rest.create_guild_text_channel()](https://docs.hikari-py.dev/en/stable/reference/hikari/api/rest/#hikari.api.rest.RESTClient.create_guild_text_channel) to create a new text channel in the guild the command is invoked in, with the given name.

!!! tip
    For a full list of all REST API requests you can make, see the [hikari reference](https://docs.hikari-py.dev/en/stable/reference/hikari/api/rest/). This list may be daunting at first, as it lists every single endpoint and their parameters.

## Using your client's cache

!!! info "Gateway only"
    This section is only relevant to those using a **Gateway** client, as REST bots **do not have a cache**.

While the REST API [can be used](https://docs.hikari-py.dev/en/stable/reference/hikari/api/rest/#hikari.api.rest.RESTClient.fetch_channel) to fetch data from Discord directly, this is generally **not recommended**, as it is very slow, consumes [ratelimits](https://discord.com/developers/docs/topics/rate-limits) and is generally inefficient. Instead, you should use your client's cache implementation. To access objects stored in the cache, you need to access your gateway client's [`cache`][arc.client.GatewayClientBase.cache] module.

```py hl_lines="5"
@client.include
@arc.slash_command("roles", "List all the roles in this guild!")
async def channel_info(ctx: arc.GatewayContext) -> None:
    # This returns a mapping of {role_id: role object}
    roles = client.cache.get_roles_view_for_guild(ctx.guild_id)
    # Concatenate the mentions into a string
    role_mentions = " ".join(role.mention for role in roles.values())

    await ctx.respond(f"The roles in this guild are: {role_mentions}")
```

Here, we get all roles that exist in the guild the command was invoked in, then respond with their mentions.

!!! tip
    For a full list of all cache methods, see the [hikari reference](https://docs.hikari-py.dev/en/stable/reference/hikari/api/cache/#hikari.api.cache.Cache).
